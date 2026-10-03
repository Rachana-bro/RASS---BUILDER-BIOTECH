import { useState } from "react";
import { prepareAnalysis } from "../services/api";

type SequenceRecord = {
  read_id: string;
  sequence: string;
  tokens: number[];
  length: number;
};

type PipelineResult = {
  status: string;
  input: {
    requested_reads: number;
    processed_reads: number;
  };
  filtering: {
    input_reads: number;
    passed_reads: number;
    failed_reads: number;
    pass_rate: number;
  };
  sequences: SequenceRecord[];
  model: {
    status: string;
    model_name: string;
    message: string;
  } | null;
};

type PipelineStage4Props = {
  onSelectSequenceForStage5?: (sequence: string, readId: string) => void;
};

export default function PipelineStage4({ onSelectSequenceForStage5 }: PipelineStage4Props = {}) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<PipelineResult | null>(null);
  const [selectedReadIndex, setSelectedReadIndex] = useState(0);

  async function handleRunPipeline() {
    try {
      setLoading(true);
      setError("");
      const data = await prepareAnalysis("data/demo/sample.fastq", 1000, 20);
      setResult(data);
      setSelectedReadIndex(0);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Pipeline preparation failed."
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <section
      style={{
        marginTop: "36px",
        background: "#ffffff",
        border: "1px solid #e2e8f0",
        borderRadius: "12px",
        padding: "28px",
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          flexWrap: "wrap",
          gap: "16px",
          marginBottom: "20px",
        }}
      >
        <div>
          <div
            style={{
              fontSize: "12px",
              fontWeight: 700,
              letterSpacing: "0.08em",
              color: "#3b82f6",
            }}
          >
            STAGE 4 PIPELINE FOUNDATION
          </div>
          <h2
            style={{
              margin: "6px 0",
              fontSize: "24px",
              color: "#0f172a",
            }}
          >
            DNA Preprocessing &amp; Model Interface
          </h2>
          <p
            style={{
              color: "#64748b",
              margin: 0,
              maxWidth: "650px",
              fontSize: "14px",
            }}
          >
            Real pipeline converting raw FASTQ through read filtering, sequence
            normalization, and DNA tokenization ready for the Stage 5
            Transformer model contract.
          </p>
        </div>

        <button
          type="button"
          id="btn-prepare-analysis"
          onClick={handleRunPipeline}
          disabled={loading}
          style={{
            padding: "10px 22px",
            background: loading ? "#94a3b8" : "#059669",
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
          {loading ? "PREPARING PIPELINE..." : "PREPARE ANALYSIS (DEMO FASTQ)"}
        </button>
      </div>

      {error && (
        <div
          style={{
            marginBottom: "20px",
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

      {/* PIPELINE ARCHITECTURE FLOW DIAGRAM */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "8px",
          padding: "14px 18px",
          background: "#f8fafc",
          borderRadius: "8px",
          border: "1px solid #e2e8f0",
          fontSize: "12px",
          fontWeight: 600,
          color: "#475569",
          marginBottom: "24px",
        }}
      >
        <span style={{ color: "#2563eb" }}>FASTQ Upload</span>
        <span>→</span>
        <span style={{ color: "#2563eb" }}>Parser</span>
        <span>→</span>
        <span style={{ color: "#059669" }}>Quality Filter</span>
        <span>→</span>
        <span style={{ color: "#059669" }}>DNA Normalizer</span>
        <span>→</span>
        <span style={{ color: "#7c3aed" }}>DNA Tokenizer</span>
        <span>→</span>
        <span style={{ color: "#d97706" }}>Model Contract (Stage 4)</span>
        <span>→</span>
        <span style={{ color: "#7c3aed", fontWeight: 700 }}>Transformer (Stage 5)</span>
      </div>

      {result && (
        <div>
          {/* METRIC CARDS */}
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
              gap: "14px",
              marginBottom: "24px",
            }}
          >
            <div
              style={{
                background: "#f8fafc",
                border: "1px solid #e2e8f0",
                borderRadius: "8px",
                padding: "14px",
              }}
            >
              <div style={{ fontSize: "11px", color: "#64748b", fontWeight: 700 }}>
                PROCESSED READS
              </div>
              <div style={{ fontSize: "22px", fontWeight: 800, marginTop: "4px" }}>
                {result.input.processed_reads} / {result.input.requested_reads}
              </div>
            </div>

            <div
              style={{
                background: "#f0fdf4",
                border: "1px solid #bbf7d0",
                borderRadius: "8px",
                padding: "14px",
              }}
            >
              <div style={{ fontSize: "11px", color: "#166534", fontWeight: 700 }}>
                FILTER PASSED
              </div>
              <div style={{ fontSize: "22px", fontWeight: 800, color: "#15803d", marginTop: "4px" }}>
                {result.filtering.passed_reads} ({result.filtering.pass_rate}%)
              </div>
            </div>

            <div
              style={{
                background: "#f8fafc",
                border: "1px solid #e2e8f0",
                borderRadius: "8px",
                padding: "14px",
              }}
            >
              <div style={{ fontSize: "11px", color: "#64748b", fontWeight: 700 }}>
                FILTER FAILED
              </div>
              <div style={{ fontSize: "22px", fontWeight: 800, color: "#64748b", marginTop: "4px" }}>
                {result.filtering.failed_reads}
              </div>
            </div>

            <div
              style={{
                background: "#eff6ff",
                border: "1px solid #bfdbfe",
                borderRadius: "8px",
                padding: "14px",
              }}
            >
              <div style={{ fontSize: "11px", color: "#1e40af", fontWeight: 700 }}>
                TOKENIZED SEQUENCES
              </div>
              <div style={{ fontSize: "22px", fontWeight: 800, color: "#1d4ed8", marginTop: "4px" }}>
                {result.sequences.length}
              </div>
            </div>
          </div>

          {/* MODEL CONTRACT BOX */}
          {result.model && (
            <div
              style={{
                background: "#fffbeb",
                border: "1px solid #fde68a",
                borderRadius: "8px",
                padding: "16px 20px",
                marginBottom: "24px",
              }}
            >
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  flexWrap: "wrap",
                  gap: "10px",
                }}
              >
                <div>
                  <span
                    style={{
                      fontSize: "11px",
                      fontWeight: 700,
                      background: "#fef3c7",
                      color: "#b45309",
                      padding: "3px 8px",
                      borderRadius: "4px",
                      marginRight: "8px",
                    }}
                  >
                    MODEL INTERFACE CONTRACT
                  </span>
                  <strong style={{ fontSize: "14px", color: "#92400e" }}>
                    {result.model.model_name}
                  </strong>
                </div>
                <div
                  style={{
                    fontSize: "12px",
                    fontWeight: 700,
                    color: "#b45309",
                    background: "#fef3c7",
                    padding: "4px 10px",
                    borderRadius: "12px",
                    border: "1px solid #fcd34d",
                  }}
                >
                  STATUS: {result.model.status.toUpperCase()}
                </div>
              </div>
              <p
                style={{
                  fontSize: "13px",
                  color: "#78350f",
                  margin: "8px 0 0 0",
                  fontStyle: "italic",
                }}
              >
                &ldquo;{result.model.message}&rdquo;
              </p>
            </div>
          )}

          {/* SEQUENCES & TOKEN PREVIEW */}
          <div>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginBottom: "12px",
              }}
            >
              <h3 style={{ margin: 0, fontSize: "16px", color: "#0f172a" }}>
                Tokenized DNA Sequences (Stage 4 Output)
              </h3>
              <div style={{ fontSize: "12px", color: "#64748b" }}>
                Vocabulary: A=1, C=2, G=3, T=4, N=5, PAD=0
              </div>
            </div>

            {/* Read selector tabs */}
            <div
              style={{
                display: "flex",
                gap: "8px",
                marginBottom: "16px",
                overflowX: "auto",
                paddingBottom: "4px",
              }}
            >
              {result.sequences.map((seq, idx) => (
                <button
                  key={seq.read_id}
                  type="button"
                  onClick={() => setSelectedReadIndex(idx)}
                  style={{
                    padding: "6px 12px",
                    fontSize: "12px",
                    fontWeight: selectedReadIndex === idx ? 700 : 500,
                    borderRadius: "6px",
                    border:
                      selectedReadIndex === idx
                        ? "1px solid #3b82f6"
                        : "1px solid #e2e8f0",
                    background:
                      selectedReadIndex === idx ? "#eff6ff" : "#f8fafc",
                    color:
                      selectedReadIndex === idx ? "#1d4ed8" : "#475569",
                    cursor: "pointer",
                  }}
                >
                  {seq.read_id} ({seq.length} bp)
                </button>
              ))}
            </div>

            {/* Selected Read Details */}
            {result.sequences[selectedReadIndex] && (
              <div
                style={{
                  background: "#0f172a",
                  color: "#f8fafc",
                  borderRadius: "8px",
                  padding: "18px 20px",
                  fontFamily: "Consolas, Monaco, monospace",
                  fontSize: "13px",
                  lineHeight: "1.6",
                }}
              >
                <div style={{ color: "#94a3b8", fontSize: "11px", marginBottom: "6px" }}>
                  // READ ID: {result.sequences[selectedReadIndex].read_id} | LENGTH:{" "}
                  {result.sequences[selectedReadIndex].length} bp
                </div>

                <div style={{ marginBottom: "12px" }}>
                  <div style={{ color: "#38bdf8", fontSize: "12px" }}>
                    NORMALIZED SEQUENCE:
                  </div>
                  <div
                    style={{
                      letterSpacing: "0.1em",
                      wordBreak: "break-all",
                      fontSize: "14px",
                      color: "#4ade80",
                    }}
                  >
                    {result.sequences[selectedReadIndex].sequence}
                  </div>
                </div>

                <div>
                  <div style={{ color: "#f472b6", fontSize: "12px" }}>
                    INTEGER TOKENS (FEED TO MODEL):
                  </div>
                  <div
                    style={{
                      color: "#fde047",
                      wordBreak: "break-all",
                      background: "#1e293b",
                      padding: "8px 12px",
                      borderRadius: "6px",
                      marginTop: "4px",
                      fontSize: "12px",
                    }}
                  >
                    [{result.sequences[selectedReadIndex].tokens.join(", ")}]
                  </div>
                </div>

                {onSelectSequenceForStage5 && (
                  <button
                    type="button"
                    onClick={() => {
                      onSelectSequenceForStage5(
                        result.sequences[selectedReadIndex].sequence,
                        result.sequences[selectedReadIndex].read_id
                      );
                      document.getElementById("stage5-container")?.scrollIntoView({ behavior: "smooth" });
                    }}
                    style={{
                      marginTop: "14px",
                      padding: "7px 14px",
                      background: "#7c3aed",
                      color: "#ffffff",
                      border: "none",
                      borderRadius: "6px",
                      fontSize: "12px",
                      fontWeight: 700,
                      cursor: "pointer",
                      display: "inline-flex",
                      alignItems: "center",
                      gap: "6px",
                    }}
                  >
                    <span>ANALYZE THIS READ IN STAGE 5 TRANSFORMER</span>
                    <span>→</span>
                  </button>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </section>
  );
}
