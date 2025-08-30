# backend/app/routes/analyze.py
from __future__ import annotations

from fastapi import APIRouter, UploadFile, File, HTTPException
import tempfile, zipfile, os, time
import networkx as nx
import re

router = APIRouter()

# Safety limits
MAX_FILES = 5000
MAX_TOTAL_BYTES = 50 * 1024 * 1024  # 50 MB

# Supported extensions by type
FILE_TYPES = {
    "python": [".py"],
    "cpp": [".c", ".cpp", ".h", ".hpp"],
    "java": [".java"],
    "web": [".html", ".htm", ".css", ".js", ".jsx", ".ts", ".tsx"],
}

# Extract ZIP safely
def _safe_extract_zip(zip_path: str, dest_dir: str) -> None:
    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
        if len(names) > MAX_FILES:
            raise HTTPException(status_code=400, detail="Too many files in zip.")
        total = sum(i.file_size for i in zf.infolist())
        if total > MAX_TOTAL_BYTES:
            raise HTTPException(status_code=413, detail="Zip too large.")

        for info in zf.infolist():
            norm = os.path.normpath(info.filename)
            if norm.startswith("..") or os.path.isabs(norm):
                raise HTTPException(status_code=400, detail="Invalid zip entry path.")
            # Skip symlinks
            if (info.external_attr >> 16) & 0o120000 == 0o120000:
                continue
            zf.extract(info, dest_dir)

# Collect all files with supported extensions
def get_code_files(root: str) -> list[str]:
    files = []
    for dirpath, _, filenames in os.walk(root):
        for fname in filenames:
            ext = os.path.splitext(fname)[1].lower()
            if any(ext in exts for exts in FILE_TYPES.values()):
                files.append(os.path.join(dirpath, fname))
    return files

# Extract dependencies from files
def extract_dependencies(fpath: str, ftype: str) -> list[str]:
    deps = []
    try:
        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        if ftype == "python":
            imports = re.findall(r'^\s*(?:from\s+([\w\.]+)|import\s+([\w\.]+))', content, re.MULTILINE)
            for fr, im in imports:
                deps.append(fr or im)
        elif ftype in ("cpp", "c"):
            includes = re.findall(r'#include\s+[<"]([\w\.]+)[>"]', content)
            deps.extend(includes)
        elif ftype == "java":
            imports = re.findall(r'import\s+([\w\.]+);', content)
            deps.extend(imports)
        elif ftype in ("web", "jsx", "tsx", "ts", "js"):
            # JS/TS imports
            js_imports = re.findall(r'import\s+(?:[\w{}\s,*]+from\s+)?["\'](.*?)["\']', content)
            js_requires = re.findall(r'require\(["\'](.*?)["\']\)', content)
            # HTML scripts/links
            html_scripts = re.findall(r'<script\s+.*?src=["\'](.*?)["\']', content, re.IGNORECASE)
            html_links = re.findall(r'<link\s+.*?href=["\'](.*?)["\']', content, re.IGNORECASE)
            deps.extend(js_imports + js_requires + html_scripts + html_links)
    except Exception:
        pass
    return deps

# Map file extension to type
def get_file_type(fpath: str) -> str:
    ext = os.path.splitext(fpath)[1].lower()
    for ftype, exts in FILE_TYPES.items():
        if ext in exts:
            return ftype
    return "unknown"


@router.post("/analyze")
async def analyze_code(file: UploadFile = File(...)):
    t0 = time.perf_counter()

    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = os.path.join(tmpdir, file.filename)
        with open(zip_path, "wb") as f:
            f.write(await file.read())

        try:
            _safe_extract_zip(zip_path, tmpdir)
        except zipfile.BadZipFile:
            raise HTTPException(status_code=400, detail="Invalid ZIP file.")

        code_files = get_code_files(tmpdir)
        if not code_files:
            return {"nodes": [], "edges": [], "meta": {
                "internal_files": 0, "external_pkgs": 0, "skipped_files": 0,
                "cycles": [], "duration_ms": int((time.perf_counter() - t0) * 1000)
            }}

        g = nx.DiGraph()
        internal_nodes = set()
        external_nodes = set()
        skipped = 0

        # Build graph
        for fpath in code_files:
            rel_path = os.path.relpath(fpath, tmpdir).replace("\\", "/")
            ftype = get_file_type(fpath)
            g.add_node(rel_path, type=ftype, label=os.path.basename(rel_path))
            internal_nodes.add(rel_path)

            deps = extract_dependencies(fpath, ftype)
            if deps is None:
                skipped += 1
                continue

            for dep in deps:
                if not dep:
                    continue
                target_file = None
                # Relative imports resolve to internal files
                if dep.startswith(".") or os.path.basename(dep) in [os.path.basename(cf) for cf in code_files]:
                    for cf in code_files:
                        if os.path.basename(cf) == os.path.basename(dep):
                            target_file = os.path.relpath(cf, tmpdir).replace("\\", "/")
                            break
                if target_file:
                    g.add_node(target_file, type=get_file_type(target_file), label=os.path.basename(target_file))
                    g.add_edge(rel_path, target_file, kind="import", external=False)
                else:
                    dep_name = os.path.basename(dep).split(".")[0]
                    g.add_node(dep_name, type="external", label=dep_name)
                    g.add_edge(rel_path, dep_name, kind="import", external=True)
                    external_nodes.add(dep_name)

        # Compute cycles for internal-only subgraph
        internal_sub = g.subgraph([n for n, d in g.nodes(data=True) if d.get("type") != "external"])
        cycles = []
        try:
            for i, cyc in enumerate(nx.simple_cycles(internal_sub)):
                if i >= 25:
                    break
                cycles.append([str(x) for x in cyc])
        except nx.NetworkXNoCycle:
            cycles = []

        # Prepare response
        nodes = [{"id": n, "label": d.get("label", n), "type": d.get("type", "file")} for n, d in g.nodes(data=True)]
        edges = [{"id": f"{u}->{v}", "source": u, "target": v, "kind": d.get("kind", "import"), "external": bool(d.get("external", False))}
                 for u, v, d in g.edges(data=True)]
        meta = {
            "internal_files": len(internal_nodes),
            "external_pkgs": len(external_nodes),
            "skipped_files": skipped,
            "cycles": cycles,
            "duration_ms": int((time.perf_counter() - t0) * 1000),
        }

        return {"nodes": nodes, "edges": edges, "meta": meta}
