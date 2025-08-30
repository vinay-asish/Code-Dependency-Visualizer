// frontend/src/App.tsx
import { useMemo, useState } from "react";
import FileUploader from "./components/FileUploader";
import GraphView from "./components/GraphView";
import type { GraphData } from "./services/api";
import "./App.css";

export default function App() {
  const [graph, setGraph] = useState<GraphData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showExternal, setShowExternal] = useState(true);
  const [showInits, setShowInits] = useState(false);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const cycles = useMemo(() => graph?.meta?.cycles ?? [], [graph]);

  return (
    <div className="shell">
      <h1>📚 Dependency Visualizer</h1>
      <p className="subtitle">
        Upload a .zip of your Python codebase. Backend parses imports and returns a dependency graph.
      </p>

      <div className="toolbar">
        <FileUploader onResult={setGraph} onError={setError} />
        <div className="spacer" />
        <label className="toggle">
          <input
            type="checkbox"
            checked={showExternal}
            onChange={(e) => setShowExternal(e.target.checked)}
          />
          Show external packages
        </label>
        <label className="toggle">
          <input
            type="checkbox"
            checked={showInits}
            onChange={(e) => setShowInits(e.target.checked)}
          />
          Show __init__.py
        </label>
      </div>

      {error && <div className="error">{error}</div>}

      {graph ? (
        <>
          <GraphView
            data={graph}
            options={{ showExternal, showInits, highlightCycles: cycles }}
            onSelect={setSelectedId}
          />

          <div className="meta">
            <div>
              <strong>Internal files:</strong> {graph.meta?.internal_files ?? 0}
            </div>
            <div>
              <strong>External packages:</strong> {graph.meta?.external_pkgs ?? 0}
            </div>
            <div>
              <strong>Skipped files:</strong> {graph.meta?.skipped_files ?? 0}
            </div>
            <div>
              <strong>Analyze time:</strong> {graph.meta?.duration_ms ?? 0} ms
            </div>
          </div>

          <div className="panel-grid">
            <div className="panel">
              <h3>Node details</h3>
              {selectedId ? (
                <div className="mono">{selectedId}</div>
              ) : (
                <div className="muted">Select a node in the graph…</div>
              )}
            </div>
            <div className="panel">
              <h3>Cycles (first {cycles.length})</h3>
              {cycles.length === 0 ? (
                <div className="muted">No cycles detected.</div>
              ) : (
                <ul className="mono">
                  {cycles.map((c, i) => (
                    <li key={i}>{c.join(" → ")}</li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        </>
      ) : (
        <div className="panel help">No graph yet — upload a .zip to analyze.</div>
      )}
    </div>
  );
}
