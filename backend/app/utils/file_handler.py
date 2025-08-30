# backend/app/utils/file_handler.py
from __future__ import annotations
import os
import ast
from typing import Iterable, List, Set, Tuple

# Directories we will *not* descend into while scanning
SKIP_DIRS: Set[str] = {
    "__pycache__", "venv", ".venv", ".git", "node_modules", "dist",
    "build", "site-packages", ".mypy_cache", ".pytest_cache"
}

# Top-level folders (relative to extraction root) that we allow scanning
DEFAULT_ALLOWED_ROOTS: Set[str] = {"backend"}


def _is_under_allowed_root(root_dir: str, dirpath: str, allowed_roots: Set[str]) -> bool:
    rel = os.path.relpath(dirpath, root_dir)
    if rel == ".":
        return True
    top = rel.split(os.sep, 1)[0]
    return top in allowed_roots


def get_python_files(root_dir: str, allowed_roots: Iterable[str] | None = None) -> List[str]:
    """
    Recursively list .py files under root_dir, skipping vendor/virtualenv/etc.
    Only walks inside folders listed in allowed_roots (defaults to {"backend"}).
    """
    allowed: Set[str] = set(allowed_roots) if allowed_roots else set(DEFAULT_ALLOWED_ROOTS)
    py_files: List[str] = []

    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Keep walking only inside allowed roots
        if not _is_under_allowed_root(root_dir, dirpath, allowed):
            dirnames[:] = []  # stop descending
            continue

        # Filter out unwanted directories
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]

        for name in filenames:
            if name.endswith(".py"):
                py_files.append(os.path.join(dirpath, name))
    return py_files


def module_name_from_path(root_dir: str, file_path: str) -> str:
    """
    Convert a file path to a Python module name rooted at the extraction root.
    Examples:
      backend/app/main.py -> backend.app.main
      backend/app/__init__.py -> backend.app
    """
    rel_path = os.path.relpath(file_path, root_dir)
    if rel_path.endswith(".py"):
        rel_path = rel_path[:-3]
    parts = rel_path.split(os.sep)
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(p for p in parts if p)


def _read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def extract_imports(path: str, current_module: str) -> List[str]:
    """
    Parse a Python file and return a list of *module names* it imports.
    Handles absolute and relative imports. Skips syntax errors gracefully.
    """
    source = _read_text(path)
    try:
        tree = ast.parse(source, filename=path)
    except SyntaxError:
        return []

    imports: Set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name:
                    imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            base = node.module or ""
            if node.level:  # handle relative imports like "from . import x" or "from ..pkg import y"
                cur_parts = current_module.split(".")
                # go up "level" packages
                up = cur_parts[:-node.level] if node.level <= len(cur_parts) else []
                if base:
                    full = ".".join(up + [base])
                else:
                    full = ".".join(up)  # "from . import x" -> current package
                if full:
                    imports.add(full)
            else:
                if base:
                    imports.add(base)

    return sorted(imports)
