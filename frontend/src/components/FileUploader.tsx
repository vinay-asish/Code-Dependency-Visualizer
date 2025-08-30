// frontend/src/components/FileUploader.tsx
import React, { useRef, useState } from "react";
import { analyzeZip } from "../services/api";
import type { GraphData } from "../services/api";


type Props = {
  onResult: (data: GraphData) => void;
  onError?: (msg: string) => void;
};

const FileUploader: React.FC<Props> = ({ onResult, onError }) => {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [busy, setBusy] = useState(false);

  const handlePick = () => inputRef.current?.click();

  const handleChange: React.ChangeEventHandler<HTMLInputElement> = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setBusy(true);
    try {
      const data = await analyzeZip(file);
      onResult(data);
    } catch (err: any) {
      const msg =
        err?.response?.data?.detail ||
        err?.message ||
        "Upload failed. Please try again.";
      onError?.(msg);
    } finally {
      setBusy(false);
      e.target.value = ""; // allow re-select same file
    }
  };

  return (
    <div className="uploader">
      <input
        ref={inputRef}
        type="file"
        accept=".zip"
        onChange={handleChange}
        style={{ display: "none" }}
      />
      <button className="btn" onClick={handlePick} disabled={busy}>
        {busy ? "Analyzing…" : "Upload .zip"}
      </button>
    </div>
  );
};

export default FileUploader;
