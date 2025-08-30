import React, { useEffect, useRef } from "react";
import cytoscape from "cytoscape";
import type { Core, ElementDefinition } from "cytoscape";
import type { GraphData } from "../services/api";

export type GraphOptions = {
  showExternal: boolean;
  showInits: boolean;
  highlightCycles: string[][];
};

type Props = {
  data: GraphData;
  options: GraphOptions;
  onSelect?: (id: string | null) => void;
};

const layoutOpts = { name: "cose", fit: true, animate: false } as const;

// --- Helper to ensure IDs are valid strings ---
const safeId = (val: string | undefined | null): string | null => {
  if (!val || typeof val !== "string") return null;
  const trimmed = val.trim();
  return trimmed.length > 0 ? trimmed : null;
};

const GraphView: React.FC<Props> = ({ data, options, onSelect }) => {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const cyRef = useRef<Core | null>(null);

  // Convert GraphData -> Cytoscape elements with filtering
  const toElements = (): ElementDefinition[] => {
    const els: ElementDefinition[] = [];
    const allowNode = (type: string, label: string) => {
      if (!options.showExternal && type === "external") return false;
      if (!options.showInits && label === "__init__.py") return false;
      return true;
    };

    const nodeMap = new Map<string, { label: string; type: string }>();
    for (const n of data.nodes) {
      const sid = safeId(n.id);
      if (!sid) continue;
      if (allowNode(n.type, n.label)) nodeMap.set(sid, { label: n.label, type: n.type });
    }

    for (const [id, meta] of nodeMap) {
      els.push({
        data: { id, label: meta.label, type: meta.type },
      });
    }

    for (const e of data.edges) {
      const sid = safeId(e.source);
      const tid = safeId(e.target);
      const eid = safeId(e.id);
      if (!sid || !tid || !eid) continue; // skip invalid
      if (!nodeMap.has(sid)) continue;
      if (!nodeMap.has(tid) && !(options.showExternal && e.external)) continue;
      els.push({
        data: {
          id: eid,
          source: sid,
          target: tid,
          kind: e.kind,
          external: !!e.external,
        },
      });
    }

    return els;
  };

  useEffect(() => {
    if (!containerRef.current) return;

    // Create instance once
    if (!cyRef.current) {
      cyRef.current = cytoscape({
        container: containerRef.current,
        elements: [],
        style: [
          {
            selector: "node",
            style: {
              "background-color": "#6aa3ff",
              "label": "data(label)",
              "font-size": 10,
              "text-wrap": "wrap",
              "text-max-width": "120px",
              "text-valign": "center",
              "color": "#cfe0ff",
              "border-width": 1,
              "border-color": "#2e436f",
              "width": 36,
              "height": 36,
            },
          },
          {
            selector: 'node[type = "external"]',
            style: {
              "shape": "round-rectangle",
              "background-color": "#7b7f8a",
              "color": "#e6e6e6",
              "width": 28,
              "height": 24,
            },
          },
          {
            selector: "edge",
            style: {
              "curve-style": "bezier",
              "width": 1.5,
              "line-color": "#7aa0d0",
              "target-arrow-shape": "triangle",
              "target-arrow-color": "#7aa0d0",
              "arrow-scale": 0.8,
            },
          },
          {
            selector: 'edge[external = 1], edge[external = true]',
            style: {
              "line-style": "dashed",
              "opacity": 0.85,
            },
          },
          {
            selector: ".cycle",
            style: { "background-color": "#ff7a7a", "border-color": "#aa3b3b" },
          },
          { selector: ":selected", style: { "border-width": 3, "border-color": "#fff" } },
        ],
      });

      cyRef.current.on("select", "node", (evt) => onSelect?.(evt.target.id()));
      cyRef.current.on("unselect", "node", () => onSelect?.(null));
    }

    const cy = cyRef.current;
    cy.elements().remove();
    cy.add(toElements());
    cy.layout(layoutOpts as any).run();

    // Highlight cycles if provided
    cy.nodes().removeClass("cycle");
    for (const cyc of options.highlightCycles || []) {
      cyc.forEach((id) => cy.$id(id).addClass("cycle"));
    }

    // Fit after render
    cy.fit(undefined, 20);
  }, [data, options]); // eslint-disable-line react-hooks/exhaustive-deps

  return <div ref={containerRef} style={{ width: "100%", height: 560, borderRadius: 12 }} />;
};

export default GraphView;
