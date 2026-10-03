import { useState } from "react";
import { uploadFastq } from "../services/api";

type Props = {
  onComplete: (result: any) => void;
};

export default function FastqUpload({ onComplete }: Props) {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleUpload() {
    if (!file) {
      setError("Please select a FASTQ file.");
      return;
    }

    try {
      setLoading(true);
      setError("");

      const result = await uploadFastq(file);
      onComplete(result);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Upload failed."
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ marginTop: "24px" }}>
      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          alignItems: "center",
          gap: "14px",
        }}
      >
        <input
          type="file"
          accept=".fastq,.fq,.fastq.gz,.fq.gz"
          id="fastq-file-input"
          style={{
            padding: "8px 12px",
            border: "1px solid #cbd5e1",
            borderRadius: "8px",
            background: "#f8fafc",
            fontSize: "14px",
            color: "#334155",
            cursor: "pointer",
          }}
          onChange={(event) => {
            const selected = event.target.files?.[0] || null;
            setFile(selected);
            if (selected) setError("");
          }}
        />

        <button
          type="button"
          onClick={handleUpload}
          disabled={loading}
          style={{
            padding: "10px 22px",
            background: loading ? "#94a3b8" : "#2563eb",
            color: "#ffffff",
            border: "none",
            borderRadius: "8px",
            fontSize: "13px",
            fontWeight: 700,
            letterSpacing: "0.04em",
            cursor: loading ? "not-allowed" : "pointer",
            boxShadow: "0 1px 3px rgba(0,0,0,0.1)",
            transition: "background 0.2s",
          }}
        >
          {loading ? "Analyzing..." : "ANALYZE FASTQ"}
        </button>
      </div>

      {file && (
        <div
          style={{
            marginTop: "10px",
            fontSize: "13px",
            color: "#64748b",
          }}
        >
          Selected: <strong>{file.name}</strong> ({(file.size / 1024).toFixed(1)} KB)
        </div>
      )}

      {error && (
        <div
          style={{
            marginTop: "14px",
            padding: "10px 14px",
            background: "#fef2f2",
            border: "1px solid #fecaca",
            borderRadius: "8px",
            color: "#b91c1c",
            fontSize: "13px",
            fontWeight: 500,
          }}
        >
          {error}
        </div>
      )}
    </div>
  );
}
