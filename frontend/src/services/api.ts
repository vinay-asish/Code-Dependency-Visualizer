// frontend/src/services/api.ts
import axios from "axios";

export type GraphNode = {
  id: string;
  label: string;
  type: "file" | "external";
};

export type GraphEdge = {
  id: string;
  source: string;
  target: string;
  kind: "import";
  external?: boolean;
};

export type GraphMeta = {
  internal_files: number;
  external_pkgs: number;
  skipped_files: number;
  cycles: string[][];
  duration_ms: number;
};

export type GraphData = {
  nodes: GraphNode[];
  edges: GraphEdge[];
  meta?: GraphMeta;
};

const BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.toString() || "http://localhost:8000/api";

export const api = axios.create({
  baseURL: BASE_URL,
});

export async function analyzeZip(file: File): Promise<GraphData> {
  const formData = new FormData();
  formData.append("file", file);

  const res = await api.post<GraphData>("/analyze", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });

  return res.data;
}
