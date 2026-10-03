import { useState } from "react";
import { analyzeDnaSequence, type Stage5Result } from "../services/api";

type Props = {
  initialSequence?: string;
  initialReadId?: string;
  onAnalysisComplete?: (result: Stage5Result) => void;
};

const DEMO_PRESETS = [
  {
    name: "Demo Read 001 (Canonical)",
    seq: "ACGTACGTACGTACGTACGT",
    desc: "Stage 4 first passed read",
  },
  {
    name: "BRCA1 Exon 20 Focus (Wildtype)",
    seq: "ATGGATTTATCTGCTCTTCGCGTTGAAGAAGTACAAAATGTCATTAATGCTATGCAGAAA",
    desc: "60 bp canonical reading window",
  },
  {
    name: "EGFR Exon 21 Segment",
    seq: "AGATCACAGATTTTGGGCGGGCCAAACTGCTGGGTGCGGAAGAGAAAGAATACCATGCAG",
    desc: "Targeted oncology locus",
  },
  {
    name: "Sequence with Unknowns & Lowercase",
    seq: "acgtNNacgtXyZtacgt",
    desc: "Tests normalization & <UNK> tokens",
  },
];

export default function PipelineStage5({
  initialSequence,
  initialReadId,
  onAnalysisComplete,
}: Props) {
  const [sequence, setSequence] = useState(
    initialSequence || "ACGTACGTACGTACGTACGT"
  );
  const [readId, setReadId] = useState(initialReadId || "READ_001");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<Stage5Result | null>(null);
  const [copied, setCopied] = useState(false);
  const [showRawJson, setShowRawJson] = useState(false);

  async function handleRunAnalysis() {
    if (!sequence.trim()) {
      setError("Please provide a DNA sequence to analyze.");
      return;
    }
    try {
      setLoading(true);
      setError("");
      const data = await analyzeDnaSequence(sequence.trim(), readId.trim());
      setResult(data);
      if (onAnalysisComplete) {
        onAnalysisComplete(data);
      }
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Stage 5 analysis failed."
      );
    } finally {
      setLoading(false);
    }
  }

  function handleCopyJson() {
    if (!result) return;
    navigator.clipboard.writeText(JSON.stringify(result, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  function getTokenColor(token: string) {
    switch (token) {
      case "A":
        return { bg: "#dcfce7", text: "#15803d", border: "#86efac" };
      case "C":
        return { bg: "#dbeafe", text: "#1d4ed8", border: "#93c5fd" };
      case "G":
        return { bg: "#fef3c7", text: "#b45309", border: "#fde68a" };
      case "T":
        return { bg: "#fee2e2", text: "#b91c1c", border: "#fca5a5" };
      case "<START>":
      case "<END>":
        return { bg: "#f3e8ff", text: "#7e22ce", border: "#d8b4fe" };
      case "<PAD>":
        return { bg: "#f1f5f9", text: "#64748b", border: "#cbd5e1" };
      case "<UNK>":
      default:
        return { bg: "#ffe4e6", text: "#be123c", border: "#fecdd3" };
    }
  }

  return (
    <section
      id="stage5-container"
      style={{
        marginTop: "36px",
        background: "#ffffff",
        border: "1px solid #e2e8f0",
        borderRadius: "12px",
        padding: "28px",
        boxShadow: "0 1px 3px rgba(0,0,0,0.05)",
      }}
    >
      {/* HEADER */}
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
              color: "#7c3aed",
              display: "flex",
              alignItems: "center",
              gap: "8px",
            }}
          >
            <span>STAGE 5 — DNA TRANSFORMER / AI ANALYSIS LAYER</span>
            <span
              style={{
                fontSize: "10px",
                background: "#ede9fe",
                color: "#6d28d9",
                padding: "2px 8px",
                borderRadius: "12px",
                fontWeight: 700,
              }}
            >
              TECHNICAL FOUNDATION
            </span>
          </div>
          <h2
            style={{
              margin: "6px 0",
              fontSize: "24px",
              color: "#0f172a",
            }}
          >
            PyTorch DNA Transformer &amp; Representation Engine
          </h2>
          <p
            style={{
              color: "#64748b",
              margin: 0,
              maxWidth: "750px",
              fontSize: "14px",
              lineHeight: "1.5",
            }}
          >
            Modular deep learning architecture providing genuine DNA tokenization (with special tokens),
            PyTorch Multi-Head Self-Attention encoding, latent sequence embeddings, and computational attention
            mapping with rigorous scientific validation safeguards.
          </p>
        </div>

        {/* STATUS PILLS */}
        <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
          <div
            id="badge-model-status"
            style={{
              padding: "6px 12px",
              borderRadius: "20px",
              background: "#eff6ff",
              border: "1px solid #bfdbfe",
              color: "#1d4ed8",
              fontSize: "11px",
              fontWeight: 700,
              letterSpacing: "0.04em",
            }}
          >
            MODEL: READY (PYTORCH)
          </div>
          <div
            id="badge-checkpoint-status"
            style={{
              padding: "6px 12px",
              borderRadius: "20px",
              background: "#fffbeb",
              border: "1px solid #fde68a",
              color: "#b45309",
              fontSize: "11px",
              fontWeight: 700,
              letterSpacing: "0.04em",
            }}
          >
            CHECKPOINT: NOT LOADED
          </div>
          <div
            id="badge-validation-status"
            style={{
              padding: "6px 12px",
              borderRadius: "20px",
              background: "#f1f5f9",
              border: "1px solid #cbd5e1",
              color: "#475569",
              fontSize: "11px",
              fontWeight: 700,
              letterSpacing: "0.04em",
            }}
          >
            VALIDATION REQUIRED
          </div>
        </div>
      </div>

      {/* PIPELINE ARCHITECTURE FLOW DIAGRAM */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "6px",
          padding: "12px 16px",
          background: "#f8fafc",
          borderRadius: "8px",
          border: "1px solid #e2e8f0",
          fontSize: "11px",
          fontWeight: 600,
          color: "#475569",
          marginBottom: "24px",
        }}
      >
        <span style={{ color: "#2563eb" }}>Processed DNA (Stage 4)</span>
        <span>→</span>
        <span style={{ color: "#7c3aed" }}>DNA Tokenizer</span>
        <span>→</span>
        <span style={{ color: "#7c3aed" }}>Token IDs</span>
        <span>→</span>
        <span style={{ color: "#059669" }}>DNA Transformer</span>
        <span>→</span>
        <span style={{ color: "#059669" }}>Sequence Embeddings</span>
        <span>→</span>
        <span style={{ color: "#d97706" }}>Attention Representation</span>
        <span>→</span>
        <span style={{ color: "#dc2626" }}>Pattern Detection</span>
        <span>→</span>
        <span style={{ color: "#475569" }}>Confidence Safeguard</span>
        <span>→</span>
        <span style={{ color: "#0f172a", fontWeight: 700 }}>Structured Result</span>
      </div>

      {/* INPUT WORKBENCH */}
      <div
        style={{
          background: "#f8fafc",
          border: "1px solid #e2e8f0",
          borderRadius: "10px",
          padding: "20px",
          marginBottom: "24px",
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginBottom: "12px",
            flexWrap: "wrap",
            gap: "10px",
          }}
        >
          <div style={{ fontSize: "13px", fontWeight: 700, color: "#334155" }}>
            INPUT SEQUENCE WORKBENCH
          </div>
          <div style={{ display: "flex", gap: "6px", flexWrap: "wrap" }}>
            {DEMO_PRESETS.map((preset) => (
              <button
                key={preset.name}
                type="button"
                onClick={() => {
                  setSequence(preset.seq);
                  setReadId(preset.name.split(" ")[0]);
                }}
                style={{
                  padding: "4px 10px",
                  fontSize: "11px",
                  background: "#ffffff",
                  border: "1px solid #cbd5e1",
                  borderRadius: "6px",
                  cursor: "pointer",
                  color: "#475569",
                  fontWeight: 500,
                }}
                title={preset.desc}
              >
                {preset.name}
              </button>
            ))}
          </div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr auto", gap: "12px", alignItems: "center" }}>
          <textarea
            id="stage5-sequence-input"
            value={sequence}
            onChange={(e) => setSequence(e.target.value)}
            rows={2}
            placeholder="Enter DNA sequence (A, C, G, T) or select preset above..."
            style={{
              width: "100%",
              padding: "10px 12px",
              fontFamily: "Consolas, Monaco, monospace",
              fontSize: "13px",
              borderRadius: "6px",
              border: "1px solid #cbd5e1",
              background: "#ffffff",
              color: "#0f172a",
              resize: "vertical",
              boxSizing: "border-box",
            }}
          />

          <button
            type="button"
            id="btn-run-stage5"
            onClick={handleRunAnalysis}
            disabled={loading}
            style={{
              padding: "12px 24px",
              background: loading ? "#94a3b8" : "#7c3aed",
              color: "#ffffff",
              border: "none",
              borderRadius: "8px",
              fontSize: "13px",
              fontWeight: 700,
              letterSpacing: "0.04em",
              cursor: loading ? "not-allowed" : "pointer",
              boxShadow: "0 2px 4px rgba(124, 58, 237, 0.2)",
              transition: "background 0.2s",
              whiteSpace: "nowrap",
              height: "fit-content",
            }}
          >
            {loading ? "TRANSFORMING..." : "RUN STAGE 5 TRANSFORMER"}
          </button>
        </div>

        <div
          style={{
            fontSize: "11px",
            color: "#64748b",
            marginTop: "8px",
            display: "flex",
            justifyContent: "space-between",
          }}
        >
          <span>Input Sequence Length: {sequence.trim().length} bp</span>
          <span>Target Read Identifier: {readId}</span>
        </div>
      </div>

      {error && (
        <div
          id="stage5-error-box"
          style={{
            marginBottom: "20px",
            padding: "12px 16px",
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

      {/* RESULTS DISPLAY */}
      {result && (
        <div id="stage5-results-container">
          {/* STEP 1: SUMMARY KPI CARDS */}
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
                SEQUENCE LENGTH
              </div>
              <div style={{ fontSize: "22px", fontWeight: 800, color: "#0f172a", marginTop: "4px" }}>
                {result.sequence_length} <span style={{ fontSize: "13px", fontWeight: 500 }}>bp</span>
              </div>
              <div style={{ fontSize: "11px", color: "#64748b", marginTop: "2px" }}>
                Canonical ratio: {(result.tokenizer.canonical_base_ratio * 100).toFixed(1)}%
              </div>
            </div>

            <div
              style={{
                background: "#faf5ff",
                border: "1px solid #e9d5ff",
                borderRadius: "8px",
                padding: "14px",
              }}
            >
              <div style={{ fontSize: "11px", color: "#7e22ce", fontWeight: 700 }}>
                TRANSFORMER TOKENS
              </div>
              <div style={{ fontSize: "22px", fontWeight: 800, color: "#7c3aed", marginTop: "4px" }}>
                {result.token_count}
              </div>
              <div style={{ fontSize: "11px", color: "#7e22ce", marginTop: "2px" }}>
                Incl. &lt;START&gt; &amp; &lt;END&gt;
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
              <div style={{ fontSize: "11px", color: "#1d4ed8", fontWeight: 700 }}>
                EMBEDDING DIMENSION
              </div>
              <div style={{ fontSize: "22px", fontWeight: 800, color: "#2563eb", marginTop: "4px" }}>
                {result.embedding.dimension} <span style={{ fontSize: "13px", fontWeight: 500 }}>float32</span>
              </div>
              <div style={{ fontSize: "11px", color: "#1d4ed8", marginTop: "2px" }}>
                L2 Norm: {result.embedding.norm}
              </div>
            </div>

            <div
              style={{
                background: "#fffbeb",
                border: "1px solid #fde68a",
                borderRadius: "8px",
                padding: "14px",
              }}
            >
              <div style={{ fontSize: "11px", color: "#b45309", fontWeight: 700 }}>
                MODEL CONFIDENCE
              </div>
              <div style={{ fontSize: "18px", fontWeight: 800, color: "#d97706", marginTop: "4px" }}>
                {result.confidence === null ? "NULL" : result.confidence}
              </div>
              <div style={{ fontSize: "11px", color: "#b45309", marginTop: "2px" }}>
                Validated checkpoint required
              </div>
            </div>
          </div>

          {/* STEP 2: MODEL STATUS & CHECKPOINT SAFEGUARD BANNER */}
          <div
            id="stage5-checkpoint-banner"
            style={{
              background: "#fffbeb",
              border: "1px solid #fde68a",
              borderRadius: "8px",
              padding: "16px 20px",
              marginBottom: "24px",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "10px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                <span
                  style={{
                    fontSize: "11px",
                    fontWeight: 700,
                    background: "#fef3c7",
                    color: "#b45309",
                    padding: "3px 8px",
                    borderRadius: "4px",
                  }}
                >
                  GOVERNANCE &amp; SAFETY
                </span>
                <strong style={{ fontSize: "14px", color: "#92400e" }}>
                  {result.model.checkpoint_status}
                </strong>
              </div>
              <div
                style={{
                  fontSize: "11px",
                  fontWeight: 700,
                  color: "#b45309",
                  background: "#fef3c7",
                  padding: "4px 10px",
                  borderRadius: "12px",
                  border: "1px solid #fcd34d",
                }}
              >
                FRAMEWORK: {result.model.framework.toUpperCase()} ({result.model.device.toUpperCase()})
              </div>
            </div>
            <p
              style={{
                fontSize: "12px",
                color: "#78350f",
                margin: "10px 0 0 0",
                lineHeight: "1.5",
              }}
            >
              {result.clinical_disclaimer}
            </p>
          </div>

          {/* STEP 3: DNA TOKENIZATION DETAILS */}
          <div
            style={{
              background: "#ffffff",
              border: "1px solid #e2e8f0",
              borderRadius: "8px",
              padding: "20px",
              marginBottom: "24px",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "14px" }}>
              <h3 style={{ margin: 0, fontSize: "16px", color: "#0f172a" }}>
                1. DNA Tokenizer Breakdown
              </h3>
              <div style={{ fontSize: "12px", color: "#64748b" }}>
                Special Tokens: &lt;PAD&gt;=0, &lt;UNK&gt;=1, &lt;START&gt;=2, &lt;END&gt;=3 | Nucleotides: A=4, C=5, G=6, T=7, N=8
              </div>
            </div>

            {/* Token Chips */}
            <div
              style={{
                display: "flex",
                flexWrap: "wrap",
                gap: "6px",
                padding: "14px",
                background: "#0f172a",
                borderRadius: "8px",
                maxHeight: "160px",
                overflowY: "auto",
                marginBottom: "14px",
              }}
            >
              {result.tokenizer.tokens.map((tok, idx) => {
                const color = getTokenColor(tok);
                const tid = result.tokenizer.token_ids[idx];
                return (
                  <span
                    key={`${tok}-${idx}`}
                    style={{
                      display: "inline-flex",
                      alignItems: "center",
                      gap: "4px",
                      background: color.bg,
                      color: color.text,
                      border: `1px solid ${color.border}`,
                      borderRadius: "4px",
                      padding: "2px 6px",
                      fontSize: "11px",
                      fontFamily: "Consolas, Monaco, monospace",
                      fontWeight: 700,
                    }}
                    title={`Token: ${tok} | ID: ${tid} | Index: ${idx}`}
                  >
                    <span>{tok}</span>
                    <span style={{ fontSize: "9px", opacity: 0.7 }}>#{tid}</span>
                  </span>
                );
              })}
            </div>

            {/* Raw Token ID Array */}
            <div>
              <div style={{ fontSize: "11px", fontWeight: 700, color: "#64748b", marginBottom: "4px" }}>
                TOKEN IDS ARRAY (FEED TO PYTORCH TENSOR):
              </div>
              <div
                style={{
                  background: "#f8fafc",
                  border: "1px solid #e2e8f0",
                  borderRadius: "6px",
                  padding: "8px 12px",
                  fontFamily: "Consolas, Monaco, monospace",
                  fontSize: "12px",
                  color: "#334155",
                  wordBreak: "break-all",
                }}
              >
                [{result.tokenizer.token_ids.join(", ")}]
              </div>
            </div>

            {result.tokenizer.invalid_bases.length > 0 && (
              <div
                style={{
                  marginTop: "12px",
                  padding: "8px 12px",
                  background: "#fef2f2",
                  border: "1px solid #fecaca",
                  borderRadius: "6px",
                  fontSize: "12px",
                  color: "#991b1b",
                }}
              >
                Detected {result.tokenizer.invalid_bases.length} invalid base(s) mapped to &lt;UNK&gt;:{" "}
                {result.tokenizer.invalid_bases
                  .map((inv) => `'${inv.char}' at position ${inv.position}`)
                  .join(", ")}
              </div>
            )}
          </div>

          {/* STEP 4: SEQUENCE EMBEDDINGS */}
          <div
            style={{
              background: "#ffffff",
              border: "1px solid #e2e8f0",
              borderRadius: "8px",
              padding: "20px",
              marginBottom: "24px",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "14px" }}>
              <h3 style={{ margin: 0, fontSize: "16px", color: "#0f172a" }}>
                2. Sequence Embeddings (Transformer Latent Vector)
              </h3>
              <div style={{ fontSize: "12px", color: "#64748b" }}>
                Dimension: {result.embedding.dimension} | L2 Norm: {result.embedding.norm}
              </div>
            </div>

            <p style={{ fontSize: "13px", color: "#64748b", marginTop: 0 }}>
              The numerical sequence embedding vector generated by the Transformer Encoder. Non-padding tokens
              are masked and pooled across layer activations.
            </p>

            {/* Vector sample preview */}
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(90px, 1fr))",
                gap: "8px",
                marginBottom: "12px",
              }}
            >
              {result.embedding.vector_sample.map((val, idx) => (
                <div
                  key={idx}
                  style={{
                    background: "#f1f5f9",
                    border: "1px solid #e2e8f0",
                    borderRadius: "6px",
                    padding: "6px 8px",
                    textAlign: "center",
                    fontFamily: "Consolas, Monaco, monospace",
                  }}
                >
                  <div style={{ fontSize: "9px", color: "#64748b" }}>dim[{idx}]</div>
                  <div
                    style={{
                      fontSize: "12px",
                      fontWeight: 700,
                      color: val >= 0 ? "#15803d" : "#b91c1c",
                      marginTop: "2px",
                    }}
                  >
                    {val > 0 ? `+${val.toFixed(3)}` : val.toFixed(3)}
                  </div>
                </div>
              ))}
            </div>

            <div style={{ fontSize: "11px", color: "#94a3b8", fontStyle: "italic" }}>
              Displaying first {result.embedding.vector_sample.length} of {result.embedding.dimension} dimensions.
              Full vector serialized in structured output.
            </div>
          </div>

          {/* STEP 5: ATTENTION / COMPUTATIONAL REPRESENTATION */}
          <div
            style={{
              background: "#ffffff",
              border: "1px solid #e2e8f0",
              borderRadius: "8px",
              padding: "20px",
              marginBottom: "24px",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
              <h3 style={{ margin: 0, fontSize: "16px", color: "#0f172a" }}>
                3. {result.attention.type}
              </h3>
              <span
                style={{
                  fontSize: "11px",
                  background: "#f1f5f9",
                  color: "#475569",
                  padding: "2px 8px",
                  borderRadius: "12px",
                  fontWeight: 600,
                }}
              >
                MULTI-HEAD SELF-ATTENTION
              </span>
            </div>

            <div
              style={{
                padding: "8px 12px",
                background: "#f8fafc",
                borderLeft: "3px solid #7c3aed",
                borderRadius: "4px",
                fontSize: "12px",
                color: "#475569",
                marginBottom: "16px",
              }}
            >
              {result.attention.note}
            </div>

            {/* Token Attention Weight Bars */}
            <div style={{ marginBottom: "16px" }}>
              <div style={{ fontSize: "12px", fontWeight: 700, color: "#334155", marginBottom: "8px" }}>
                Position-Wise Attention Intensity (Mean Incoming Layer Attention):
              </div>
              <div
                style={{
                  display: "flex",
                  gap: "4px",
                  overflowX: "auto",
                  paddingBottom: "8px",
                  alignItems: "flex-end",
                  height: "90px",
                }}
              >
                {result.attention.token_labels.map((lbl, idx) => {
                  const weight = result.attention.token_weights[idx] || 0.05;
                  const heightPct = Math.min(100, Math.max(15, weight * 400));
                  return (
                    <div
                      key={idx}
                      style={{
                        display: "flex",
                        flexDirection: "column",
                        alignItems: "center",
                        minWidth: "24px",
                        height: "100%",
                        justifyContent: "flex-end",
                      }}
                      title={`Pos ${idx} (${lbl}): weight ${weight.toFixed(4)}`}
                    >
                      <div
                        style={{
                          width: "18px",
                          height: `${heightPct}%`,
                          background: lbl === "<START>" || lbl === "<END>" ? "#c084fc" : "#3b82f6",
                          borderRadius: "3px 3px 0 0",
                          transition: "height 0.3s",
                        }}
                      />
                      <span
                        style={{
                          fontSize: "9px",
                          fontFamily: "Consolas, Monaco, monospace",
                          color: "#64748b",
                          marginTop: "4px",
                        }}
                      >
                        {lbl.replace("<", "").replace(">", "")}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* STEP 6: PATTERN DETECTION SAFEGUARDS */}
          <div
            style={{
              background: "#ffffff",
              border: "1px solid #e2e8f0",
              borderRadius: "8px",
              padding: "20px",
              marginBottom: "24px",
            }}
          >
            <h3 style={{ margin: "0 0 12px 0", fontSize: "16px", color: "#0f172a" }}>
              4. Pattern Detection &amp; Validation Status
            </h3>

            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
                gap: "12px",
                marginBottom: "16px",
              }}
            >
              <div style={{ background: "#f8fafc", padding: "12px", borderRadius: "6px", border: "1px solid #e2e8f0" }}>
                <div style={{ fontSize: "11px", color: "#64748b", fontWeight: 700 }}>PATTERN DETECTED</div>
                <div style={{ fontSize: "16px", fontWeight: 700, color: "#475569", marginTop: "2px" }}>
                  {result.pattern_analysis.pattern_detected ? "TRUE" : "FALSE"}
                </div>
              </div>

              <div style={{ background: "#f8fafc", padding: "12px", borderRadius: "6px", border: "1px solid #e2e8f0" }}>
                <div style={{ fontSize: "11px", color: "#64748b", fontWeight: 700 }}>ANALYSIS STATUS</div>
                <div style={{ fontSize: "16px", fontWeight: 700, color: "#d97706", marginTop: "2px" }}>
                  {result.pattern_analysis.status.toUpperCase()}
                </div>
              </div>

              <div style={{ background: "#f8fafc", padding: "12px", borderRadius: "6px", border: "1px solid #e2e8f0" }}>
                <div style={{ fontSize: "11px", color: "#64748b", fontWeight: 700 }}>CLINICAL INTERPRETATION</div>
                <div style={{ fontSize: "16px", fontWeight: 700, color: "#16a34a", marginTop: "2px" }}>
                  {result.clinical_interpretation ? "ENABLED" : "WITHHELD (SAFEGUARD)"}
                </div>
              </div>
            </div>

            <div
              style={{
                background: "#f1f5f9",
                borderRadius: "6px",
                padding: "12px 16px",
                fontSize: "12px",
                color: "#334155",
                lineHeight: "1.5",
              }}
            >
              <strong>Confidence Status:</strong> {result.confidence_display}
              <div style={{ marginTop: "4px", color: "#64748b" }}>
                RASS-BUILDER enforces strict verification: AI confidence scores and clinical classifications
                (e.g., pathogenic/benign) require supervised training and independent benchmarking on accredited
                clinical cohorts before clinical release.
              </div>
            </div>
          </div>

          {/* STEP 7: STRUCTURED OUTPUT JSON VIEWER */}
          <div
            style={{
              background: "#0f172a",
              color: "#f8fafc",
              borderRadius: "8px",
              padding: "18px 20px",
              fontFamily: "Consolas, Monaco, monospace",
            }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginBottom: "12px",
                flexWrap: "wrap",
                gap: "10px",
              }}
            >
              <div style={{ color: "#38bdf8", fontSize: "13px", fontWeight: 700 }}>
                STRUCTURED STAGE 5 RESULT OBJECT
              </div>
              <div style={{ display: "flex", gap: "8px" }}>
                <button
                  type="button"
                  onClick={() => setShowRawJson(!showRawJson)}
                  style={{
                    padding: "4px 10px",
                    background: "#1e293b",
                    color: "#f8fafc",
                    border: "1px solid #334155",
                    borderRadius: "4px",
                    fontSize: "11px",
                    cursor: "pointer",
                  }}
                >
                  {showRawJson ? "HIDE FULL JSON" : "EXPAND FULL JSON"}
                </button>
                <button
                  type="button"
                  id="btn-copy-stage5-json"
                  onClick={handleCopyJson}
                  style={{
                    padding: "4px 10px",
                    background: copied ? "#15803d" : "#2563eb",
                    color: "#ffffff",
                    border: "none",
                    borderRadius: "4px",
                    fontSize: "11px",
                    fontWeight: 600,
                    cursor: "pointer",
                  }}
                >
                  {copied ? "COPIED!" : "COPY JSON"}
                </button>
              </div>
            </div>

            <pre
              style={{
                margin: 0,
                fontSize: "12px",
                lineHeight: "1.5",
                maxHeight: showRawJson ? "600px" : "200px",
                overflowY: "auto",
                color: "#e2e8f0",
              }}
            >
              {JSON.stringify(
                {
                  stage: result.stage,
                  status: result.status,
                  sequence_length: result.sequence_length,
                  token_count: result.token_count,
                  model: result.model,
                  embedding: {
                    dimension: result.embedding.dimension,
                    generated: result.embedding.generated,
                    norm: result.embedding.norm,
                    vector_sample: result.embedding.vector_sample,
                  },
                  pattern_analysis: result.pattern_analysis,
                  confidence: result.confidence,
                  clinical_interpretation: result.clinical_interpretation,
                  attention_preview: {
                    type: result.attention.type,
                    tokens: result.attention.token_labels.slice(0, 8),
                  },
                  ...(showRawJson ? { full_result: result } : {}),
                },
                null,
                2
              )}
            </pre>
          </div>
        </div>
      )}
    </section>
  );
}
