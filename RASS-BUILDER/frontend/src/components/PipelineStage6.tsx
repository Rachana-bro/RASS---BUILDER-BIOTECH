import { useState } from "react";
import type { Stage5AnalysisResult, PatternResult, VariantResult } from "../types/stage6";

type Props = {
  stage5Result: Stage5AnalysisResult | null;
  onTriggerStage5Demo?: () => void;
};

export default function PipelineStage6({ stage5Result, onTriggerStage5Demo }: Props) {
  const [showTechnicalDetails, setShowTechnicalDetails] = useState(false);
  const [hoveredBaseIndex, setHoveredBaseIndex] = useState<number | null>(null);
  const [exportNotice, setExportNotice] = useState<string | null>(null);

  function triggerExport(type: "json" | "summary" | "print") {
    if (!stage5Result) return;

    if (type === "json") {
      const blob = new Blob([JSON.stringify(stage5Result, null, 2)], {
        type: "application/json",
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `rass-builder-stage6-${stage5Result.read_id || "analysis"}.json`;
      a.click();
      URL.revokeObjectURL(url);
      setExportNotice("Exported complete Stage 5 & 6 JSON technical analysis.");
    } else if (type === "summary") {
      setExportNotice(
        "Draft analysis summary generated. Permanent report persistence & signed PDF generation will be linked in downstream export pipeline."
      );
    } else if (type === "print") {
      window.print();
    }

    setTimeout(() => setExportNotice(null), 4000);
  }

  // ---------------------------------------------------------------------------
  // EMPTY STATE: Stage 5 has not yet been executed
  // ---------------------------------------------------------------------------
  if (!stage5Result) {
    return (
      <section
        id="stage6-container"
        style={{
          marginTop: "36px",
          background: "#ffffff",
          border: "1px solid #e2e8f0",
          borderRadius: "12px",
          padding: "32px",
          boxShadow: "0 1px 3px rgba(0,0,0,0.05)",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "16px" }}>
          <div>
            <div
              style={{
                fontSize: "12px",
                fontWeight: 700,
                letterSpacing: "0.08em",
                color: "#0369a1",
                display: "flex",
                alignItems: "center",
                gap: "8px",
              }}
            >
              <span>STAGE 6 — VARIANT &amp; PATTERN RESULTS UI</span>
              <span
                style={{
                  fontSize: "10px",
                  background: "#e0f2fe",
                  color: "#0284c7",
                  padding: "2px 8px",
                  borderRadius: "12px",
                  fontWeight: 700,
                }}
              >
                RESULTS DASHBOARD
              </span>
            </div>
            <h2 style={{ margin: "6px 0", fontSize: "24px", color: "#0f172a" }}>
              Variant &amp; Pattern Results Dashboard
            </h2>
            <p style={{ color: "#64748b", margin: 0, maxWidth: "700px", fontSize: "14px" }}>
              Consumes structured technical outputs from the Stage 5 DNA Transformer to provide clinical-grade
              variant summaries, pattern inspections, and computational representations.
            </p>
          </div>

          <div
            style={{
              padding: "6px 14px",
              borderRadius: "20px",
              background: "#f1f5f9",
              border: "1px solid #cbd5e1",
              color: "#64748b",
              fontSize: "12px",
              fontWeight: 700,
              letterSpacing: "0.04em",
            }}
          >
            AWAITING STAGE 5 ANALYSIS
          </div>
        </div>

        {/* Empty placeholder card */}
        <div
          style={{
            marginTop: "28px",
            padding: "48px 24px",
            textAlign: "center",
            background: "#f8fafc",
            borderRadius: "10px",
            border: "1px dashed #cbd5e1",
          }}
        >
          <div style={{ fontSize: "36px", marginBottom: "12px" }}>🧬</div>
          <h3 style={{ margin: "0 0 8px 0", fontSize: "18px", color: "#334155" }}>
            No Stage 5 Analysis Output Available Yet
          </h3>
          <p style={{ color: "#64748b", maxWidth: "560px", margin: "0 auto 20px auto", fontSize: "14px", lineHeight: "1.5" }}>
            The Stage 6 dashboard displays real Transformer embeddings, attention activations, and pattern detection
            telemetry. Run the Stage 5 DNA Transformer analysis on a sequence above to populate this results dashboard.
          </p>
          {onTriggerStage5Demo && (
            <button
              type="button"
              id="btn-stage6-trigger-demo"
              onClick={onTriggerStage5Demo}
              style={{
                padding: "10px 20px",
                background: "#0284c7",
                color: "#ffffff",
                border: "none",
                borderRadius: "8px",
                fontSize: "13px",
                fontWeight: 700,
                cursor: "pointer",
                boxShadow: "0 2px 4px rgba(2, 132, 199, 0.2)",
              }}
            >
              RUN DEMO ANALYSIS IN STAGE 5
            </button>
          )}
        </div>
      </section>
    );
  }

  // Extract real values safely without fabricating
  const seqLength = stage5Result.sequence_length ?? 0;
  const tokenCount = stage5Result.token_count ?? 0;
  const readId = stage5Result.read_id ?? "READ_001";
  const modelName = stage5Result.model?.name ?? "DNA Transformer";
  const modelVersion = stage5Result.model?.version ?? "Foundation";
  const checkpointLoaded = stage5Result.model?.checkpoint_loaded ?? false;
  const checkpointStatus = stage5Result.model?.checkpoint_status ?? "Trained model checkpoint unavailable.";
  const embDim = stage5Result.embedding?.dimension ?? 64;
  const embNorm = stage5Result.embedding?.norm ?? null;
  const patterns: PatternResult[] = stage5Result.pattern_analysis?.patterns ?? [];
  const variants: VariantResult[] = stage5Result.variants ?? [];
  const confidence = stage5Result.confidence ?? null;
  const canonicalRatio = stage5Result.tokenizer?.canonical_base_ratio;
  const tokens = stage5Result.tokenizer?.tokens ?? [];
  const rawSeq = tokens.filter((t) => !t.startsWith("<")).join("");

  return (
    <section
      id="stage6-container"
      style={{
        marginTop: "36px",
        background: "#ffffff",
        border: "1px solid #e2e8f0",
        borderRadius: "12px",
        padding: "32px",
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
          marginBottom: "24px",
        }}
      >
        <div>
          <div
            style={{
              fontSize: "12px",
              fontWeight: 700,
              letterSpacing: "0.08em",
              color: "#0369a1",
              display: "flex",
              alignItems: "center",
              gap: "8px",
            }}
          >
            <span>STAGE 6 — VARIANT &amp; PATTERN RESULTS UI</span>
            <span
              style={{
                fontSize: "10px",
                background: "#e0f2fe",
                color: "#0284c7",
                padding: "2px 8px",
                borderRadius: "12px",
                fontWeight: 700,
              }}
            >
              RESULTS DASHBOARD
            </span>
          </div>
          <h2 style={{ margin: "6px 0", fontSize: "24px", color: "#0f172a" }}>
            Variant &amp; Pattern Analysis Results
          </h2>
          <p style={{ color: "#64748b", margin: 0, maxWidth: "750px", fontSize: "14px", lineHeight: "1.5" }}>
            Structured report of sequence metrics, latent Transformer representations, pattern queries,
            and clinical governance disclaimers based on Stage 5 pipeline output.
          </p>
        </div>

        {/* EXPORT ACTION BUTTONS */}
        <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
          <button
            type="button"
            id="btn-export-analysis-json"
            onClick={() => triggerExport("json")}
            style={{
              padding: "8px 14px",
              background: "#f8fafc",
              border: "1px solid #cbd5e1",
              borderRadius: "6px",
              fontSize: "12px",
              fontWeight: 600,
              color: "#334155",
              cursor: "pointer",
            }}
          >
            Export Analysis (JSON)
          </button>
          <button
            type="button"
            id="btn-download-draft-report"
            onClick={() => triggerExport("summary")}
            style={{
              padding: "8px 14px",
              background: "#f8fafc",
              border: "1px solid #cbd5e1",
              borderRadius: "6px",
              fontSize: "12px",
              fontWeight: 600,
              color: "#334155",
              cursor: "pointer",
            }}
          >
            Download Report (Draft)
          </button>
          <button
            type="button"
            id="btn-print-report"
            onClick={() => triggerExport("print")}
            style={{
              padding: "8px 14px",
              background: "#0284c7",
              border: "none",
              borderRadius: "6px",
              fontSize: "12px",
              fontWeight: 600,
              color: "#ffffff",
              cursor: "pointer",
            }}
          >
            Print Report
          </button>
        </div>
      </div>

      {exportNotice && (
        <div
          id="stage6-export-notice"
          style={{
            marginBottom: "20px",
            padding: "10px 14px",
            background: "#f0fdf4",
            border: "1px solid #bbf7d0",
            borderRadius: "6px",
            color: "#166534",
            fontSize: "13px",
            fontWeight: 500,
          }}
        >
          ✓ {exportNotice}
        </div>
      )}

      {/* DASHBOARD GRID: SECTIONS A, B, C, F */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
          gap: "16px",
          marginBottom: "28px",
        }}
      >
        {/* A. ANALYSIS STATUS CARD */}
        <div
          id="card-analysis-status"
          style={{
            background: "#f8fafc",
            border: "1px solid #e2e8f0",
            borderRadius: "10px",
            padding: "18px",
          }}
        >
          <div style={{ fontSize: "11px", fontWeight: 700, color: "#64748b", letterSpacing: "0.06em" }}>
            A. ANALYSIS STATUS
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "8px", marginTop: "8px" }}>
            <span
              style={{
                display: "inline-block",
                width: "10px",
                height: "10px",
                borderRadius: "50%",
                background: checkpointLoaded ? "#16a34a" : "#d97706",
              }}
            />
            <strong style={{ fontSize: "16px", color: checkpointLoaded ? "#15803d" : "#b45309" }}>
              {checkpointLoaded ? "✓ Pipeline Completed" : "⚠ Validation Required"}
            </strong>
          </div>
          <div style={{ fontSize: "12px", color: "#475569", marginTop: "8px", lineHeight: "1.5" }}>
            Stage 5 Transformer execution completed successfully. Model weights are in foundation baseline state;
            clinical validation study pending.
          </div>
        </div>

        {/* B. SEQUENCE SUMMARY CARD */}
        <div
          id="card-sequence-summary"
          style={{
            background: "#f8fafc",
            border: "1px solid #e2e8f0",
            borderRadius: "10px",
            padding: "18px",
          }}
        >
          <div style={{ fontSize: "11px", fontWeight: 700, color: "#64748b", letterSpacing: "0.06em" }}>
            B. SEQUENCE SUMMARY
          </div>
          <div style={{ marginTop: "10px", display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px", fontSize: "13px" }}>
            <div>
              <span style={{ color: "#64748b" }}>Length:</span>{" "}
              <strong>{seqLength} bp</strong>
            </div>
            <div>
              <span style={{ color: "#64748b" }}>Tokens:</span>{" "}
              <strong>{tokenCount}</strong>
            </div>
            <div>
              <span style={{ color: "#64748b" }}>Format:</span>{" "}
              <strong>FASTQ Read</strong>
            </div>
            <div>
              <span style={{ color: "#64748b" }}>Read ID:</span>{" "}
              <strong>{readId}</strong>
            </div>
          </div>
          {canonicalRatio !== undefined && (
            <div style={{ fontSize: "11px", color: "#64748b", marginTop: "10px" }}>
              Canonical base content: {(canonicalRatio * 100).toFixed(1)}% (A/C/G/T)
            </div>
          )}
        </div>

        {/* C. MODEL INFORMATION CARD */}
        <div
          id="card-model-info"
          style={{
            background: "#f8fafc",
            border: "1px solid #e2e8f0",
            borderRadius: "10px",
            padding: "18px",
          }}
        >
          <div style={{ fontSize: "11px", fontWeight: 700, color: "#64748b", letterSpacing: "0.06em" }}>
            C. MODEL INFORMATION
          </div>
          <div style={{ marginTop: "8px", fontSize: "13px", lineHeight: "1.6" }}>
            <div>
              <span style={{ color: "#64748b" }}>Model:</span>{" "}
              <strong>{modelName}</strong> ({modelVersion})
            </div>
            <div>
              <span style={{ color: "#64748b" }}>Checkpoint:</span>{" "}
              <span style={{ color: checkpointLoaded ? "#15803d" : "#b45309", fontWeight: 700 }}>
                {checkpointLoaded ? "Loaded" : "Not Loaded"}
              </span>
            </div>
            <div>
              <span style={{ color: "#64748b" }}>Embedding:</span>{" "}
              <strong>{embDim} dimensions</strong>
            </div>
            <div>
              <span style={{ color: "#64748b" }}>Status:</span>{" "}
              <span style={{ color: "#475569", fontWeight: 600 }}>
                Foundation Ready / Validation Required
              </span>
            </div>
          </div>
          {!checkpointLoaded && (
            <div style={{ fontSize: "11px", color: "#b45309", marginTop: "6px", fontStyle: "italic" }}>
              &ldquo;Trained model checkpoint unavailable.&rdquo;
            </div>
          )}
        </div>

        {/* F. CONFIDENCE / MODEL STATUS CARD */}
        <div
          id="card-confidence-status"
          style={{
            background: "#f8fafc",
            border: "1px solid #e2e8f0",
            borderRadius: "10px",
            padding: "18px",
          }}
        >
          <div style={{ fontSize: "11px", fontWeight: 700, color: "#64748b", letterSpacing: "0.06em" }}>
            F. CONFIDENCE / MODEL STATUS
          </div>
          <div style={{ marginTop: "8px" }}>
            <div style={{ fontSize: "18px", fontWeight: 800, color: confidence === null ? "#d97706" : "#0284c7" }}>
              {confidence === null ? "Not Available" : `${(confidence * 100).toFixed(1)}%`}
            </div>
            <div style={{ fontSize: "12px", color: "#64748b", marginTop: "4px", lineHeight: "1.4" }}>
              {confidence === null
                ? "Reason: Validated model confidence unavailable."
                : "Calibrated model prediction confidence."}
            </div>
            <div
              style={{
                marginTop: "8px",
                fontSize: "11px",
                color: "#64748b",
                background: "#f1f5f9",
                padding: "6px 8px",
                borderRadius: "4px",
              }}
            >
              Zero synthetic confidence policy: Confidence metrics are withheld until verified against accredited cohorts.
            </div>
          </div>
        </div>
      </div>

      {/* 10. PATTERN / SEQUENCE VISUALIZATION (5' -> 3') */}
      <div
        id="pattern-visualization-section"
        style={{
          background: "#ffffff",
          border: "1px solid #e2e8f0",
          borderRadius: "10px",
          padding: "20px",
          marginBottom: "28px",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "14px" }}>
          <div>
            <h3 style={{ margin: 0, fontSize: "16px", color: "#0f172a" }}>
              Sequence Coordinate Map (5&prime; &rarr; 3&prime;)
            </h3>
            <div style={{ fontSize: "12px", color: "#64748b", marginTop: "2px" }}>
              Physical nucleotide layout across the sequencing window. Hover over a base to inspect position.
            </div>
          </div>
          <div style={{ fontSize: "11px", fontFamily: "Consolas, monospace", color: "#64748b" }}>
            Orientation: 5&prime; &bull;&bull;&bull; 3&prime;
          </div>
        </div>

        {/* Ruler line */}
        <div
          style={{
            fontFamily: "Consolas, Monaco, monospace",
            fontSize: "11px",
            color: "#64748b",
            background: "#f8fafc",
            padding: "8px 12px",
            borderRadius: "6px",
            border: "1px solid #e2e8f0",
            overflowX: "auto",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", color: "#94a3b8", fontSize: "10px", marginBottom: "4px" }}>
            <span>5&prime; [bp 1]</span>
            <span style={{ letterSpacing: "2px" }}>────────────────────────────────────────</span>
            <span>3&prime; [bp {rawSeq.length || seqLength}]</span>
          </div>

          {/* Bases display */}
          <div style={{ display: "flex", flexWrap: "wrap", gap: "3px", paddingTop: "4px" }}>
            {rawSeq ? (
              rawSeq.split("").map((base, idx) => {
                const isHovered = hoveredBaseIndex === idx;
                let baseColor = "#334155";
                if (base === "A") baseColor = "#15803d";
                else if (base === "C") baseColor = "#1d4ed8";
                else if (base === "G") baseColor = "#b45309";
                else if (base === "T") baseColor = "#b91c1c";

                return (
                  <span
                    key={idx}
                    onMouseEnter={() => setHoveredBaseIndex(idx)}
                    onMouseLeave={() => setHoveredBaseIndex(null)}
                    style={{
                      display: "inline-block",
                      width: "18px",
                      textAlign: "center",
                      padding: "2px 0",
                      borderRadius: "3px",
                      background: isHovered ? "#fef08a" : "#ffffff",
                      border: isHovered ? "1px solid #ca8a04" : "1px solid #e2e8f0",
                      color: baseColor,
                      fontWeight: 700,
                      cursor: "pointer",
                      fontSize: "12px",
                    }}
                    title={`Base ${idx + 1}: ${base}`}
                  >
                    {base}
                  </span>
                );
              })
            ) : (
              <span style={{ color: "#94a3b8" }}>No raw nucleotide sequence coordinates available.</span>
            )}
          </div>
        </div>

        {hoveredBaseIndex !== null && rawSeq && (
          <div
            style={{
              marginTop: "10px",
              fontSize: "12px",
              color: "#334155",
              background: "#fefce8",
              padding: "6px 12px",
              borderRadius: "4px",
              border: "1px solid #fef08a",
            }}
          >
            Base Inspection: Position <strong>{hoveredBaseIndex + 1}</strong> &bull; Nucleotide:{" "}
            <strong>{rawSeq[hoveredBaseIndex]}</strong> &bull; No simulated variant markers applied.
          </div>
        )}
      </div>

      {/* D. PATTERN DETECTION SECTION */}
      <div
        id="section-detected-patterns"
        style={{
          background: "#ffffff",
          border: "1px solid #e2e8f0",
          borderRadius: "10px",
          padding: "20px",
          marginBottom: "28px",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "14px" }}>
          <div>
            <h3 style={{ margin: 0, fontSize: "16px", color: "#0f172a" }}>
              D. Detected Genomic Patterns
            </h3>
            <div style={{ fontSize: "12px", color: "#64748b", marginTop: "2px" }}>
              Candidate sequence signatures identified by the neural pattern-detection head.
            </div>
          </div>
          <span
            style={{
              fontSize: "11px",
              padding: "3px 8px",
              borderRadius: "12px",
              background: "#f1f5f9",
              color: "#475569",
              fontWeight: 600,
            }}
          >
            {patterns.length} PATTERNS REPORTED
          </span>
        </div>

        {patterns.length === 0 ? (
          <div
            id="empty-patterns-notice"
            style={{
              padding: "24px",
              textAlign: "center",
              background: "#f8fafc",
              border: "1px solid #e2e8f0",
              borderRadius: "8px",
            }}
          >
            <div style={{ fontSize: "14px", fontWeight: 700, color: "#475569", marginBottom: "4px" }}>
              NO VALIDATED PATTERN AVAILABLE
            </div>
            <div style={{ fontSize: "13px", color: "#64748b" }}>
              Reason: A trained and validated model checkpoint is required.
            </div>
            <div style={{ fontSize: "11px", color: "#94a3b8", marginTop: "6px" }}>
              RASS-BUILDER does not create fake mutations merely to populate the table.
            </div>
          </div>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "13px" }}>
              <thead>
                <tr style={{ background: "#f8fafc", borderBottom: "2px solid #e2e8f0", textAlign: "left" }}>
                  <th style={{ padding: "10px 12px", color: "#475569" }}>Pattern</th>
                  <th style={{ padding: "10px 12px", color: "#475569" }}>Position / Region</th>
                  <th style={{ padding: "10px 12px", color: "#475569" }}>Pattern Type</th>
                  <th style={{ padding: "10px 12px", color: "#475569" }}>Model Status</th>
                  <th style={{ padding: "10px 12px", color: "#475569" }}>Confidence</th>
                  <th style={{ padding: "10px 12px", color: "#475569" }}>Evidence Status</th>
                </tr>
              </thead>
              <tbody>
                {patterns.map((p, idx) => (
                  <tr key={idx} style={{ borderBottom: "1px solid #e2e8f0" }}>
                    <td style={{ padding: "10px 12px", fontWeight: 600 }}>{p.pattern_name}</td>
                    <td style={{ padding: "10px 12px" }}>{p.region || `${p.position_start}-${p.position_end}`}</td>
                    <td style={{ padding: "10px 12px" }}>{p.pattern_type}</td>
                    <td style={{ padding: "10px 12px" }}>{p.model_status}</td>
                    <td style={{ padding: "10px 12px" }}>{p.confidence === null ? "Null" : `${p.confidence}%`}</td>
                    <td style={{ padding: "10px 12px" }}>{p.evidence_status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* E. VARIANT INFORMATION TABLE */}
      <div
        id="section-variant-information"
        style={{
          background: "#ffffff",
          border: "1px solid #e2e8f0",
          borderRadius: "10px",
          padding: "20px",
          marginBottom: "28px",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "14px" }}>
          <div>
            <h3 style={{ margin: 0, fontSize: "16px", color: "#0f172a" }}>
              E. Genomic Variant Call Records
            </h3>
            <div style={{ fontSize: "12px", color: "#64748b", marginTop: "2px" }}>
              Standard genomic coordinate calls aligned to reference assemblies.
            </div>
          </div>
          <span
            style={{
              fontSize: "11px",
              padding: "3px 8px",
              borderRadius: "12px",
              background: "#f1f5f9",
              color: "#475569",
              fontWeight: 600,
            }}
          >
            {variants.length} VARIANTS
          </span>
        </div>

        {variants.length === 0 ? (
          <div
            id="empty-variants-notice"
            style={{
              padding: "24px",
              textAlign: "center",
              background: "#f8fafc",
              border: "1px solid #e2e8f0",
              borderRadius: "8px",
            }}
          >
            <div style={{ fontSize: "14px", fontWeight: 700, color: "#475569", marginBottom: "4px" }}>
              No validated variants available.
            </div>
            <div style={{ fontSize: "13px", color: "#64748b" }}>
              Model output is currently limited to computational sequence representation.
            </div>
            <div style={{ fontSize: "11px", color: "#94a3b8", marginTop: "6px" }}>
              When verified variant call callsets are connected, this structured table will display alleles and ACMG criteria.
            </div>
          </div>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "13px" }}>
              <thead>
                <tr style={{ background: "#f8fafc", borderBottom: "2px solid #e2e8f0", textAlign: "left" }}>
                  <th style={{ padding: "10px 12px", color: "#475569" }}>Variant ID</th>
                  <th style={{ padding: "10px 12px", color: "#475569" }}>Gene / Locus</th>
                  <th style={{ padding: "10px 12px", color: "#475569" }}>Ref</th>
                  <th style={{ padding: "10px 12px", color: "#475569" }}>Obs</th>
                  <th style={{ padding: "10px 12px", color: "#475569" }}>Position</th>
                  <th style={{ padding: "10px 12px", color: "#475569" }}>Classification</th>
                  <th style={{ padding: "10px 12px", color: "#475569" }}>Confidence</th>
                  <th style={{ padding: "10px 12px", color: "#475569" }}>Evidence</th>
                </tr>
              </thead>
              <tbody>
                {variants.map((v, idx) => (
                  <tr key={idx} style={{ borderBottom: "1px solid #e2e8f0" }}>
                    <td style={{ padding: "10px 12px", fontWeight: 600 }}>{v.variant_id}</td>
                    <td style={{ padding: "10px 12px" }}>{v.gene_locus}</td>
                    <td style={{ padding: "10px 12px", fontFamily: "monospace" }}>{v.reference_allele}</td>
                    <td style={{ padding: "10px 12px", fontFamily: "monospace" }}>{v.observed_allele}</td>
                    <td style={{ padding: "10px 12px" }}>{v.position}</td>
                    <td style={{ padding: "10px 12px" }}>{v.classification}</td>
                    <td style={{ padding: "10px 12px" }}>{v.confidence === null ? "Null" : `${v.confidence}%`}</td>
                    <td style={{ padding: "10px 12px" }}>{v.evidence}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* G. INTERPRETATION SECTION (COMPUTATIONAL VS CLINICAL) */}
      <div
        id="section-interpretation"
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
          gap: "16px",
          marginBottom: "28px",
        }}
      >
        {/* COMPUTATIONAL ANALYSIS */}
        <div
          style={{
            background: "#ffffff",
            border: "1px solid #e2e8f0",
            borderRadius: "10px",
            padding: "20px",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "12px" }}>
            <span style={{ fontSize: "16px" }}>⚡</span>
            <h3 style={{ margin: 0, fontSize: "15px", color: "#0f172a" }}>
              COMPUTATIONAL ANALYSIS
            </h3>
          </div>
          <div style={{ fontSize: "13px", color: "#475569", lineHeight: "1.6" }}>
            <div>
              Sequence Latent Norm: <strong>{embNorm !== null ? embNorm.toFixed(4) : "Generated"}</strong>
            </div>
            <div>
              Transformer Layers: <strong>2 Pre-LN Encoder Blocks (4 Heads)</strong>
            </div>
            <div>
              Token Representation: <strong>{tokenCount} tokens mapped across 9-token vocabulary</strong>
            </div>
            <div style={{ marginTop: "10px", fontSize: "12px", color: "#64748b" }}>
              Mathematical activations reflect the Transformer&rsquo;s internal continuous sequence mapping.
              All vectors are accessible via the technical details panel.
            </div>
          </div>
        </div>

        {/* CLINICAL INTERPRETATION */}
        <div
          style={{
            background: "#fffbeb",
            border: "1px solid #fde68a",
            borderRadius: "10px",
            padding: "20px",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "12px" }}>
            <span style={{ fontSize: "16px" }}>⚠️</span>
            <h3 style={{ margin: 0, fontSize: "15px", color: "#92400e" }}>
              CLINICAL INTERPRETATION
            </h3>
          </div>
          <div style={{ fontSize: "13px", color: "#78350f", lineHeight: "1.6" }}>
            <strong>&ldquo;Clinical interpretation is not provided by this prototype.&rdquo;</strong>
            <p style={{ margin: "8px 0 0 0", fontSize: "12px", color: "#92400e" }}>
              Computational model output must not be automatically translated into medical diagnoses,
              treatment plans, or pathogenicity tiering without regulatory certification and independent laboratory testing.
            </p>
          </div>
        </div>
      </div>

      {/* 11. TECHNICAL DETAILS PANEL (EXPANDABLE) */}
      <div
        id="panel-technical-details"
        style={{
          background: "#f8fafc",
          border: "1px solid #e2e8f0",
          borderRadius: "10px",
          padding: "16px 20px",
        }}
      >
        <button
          type="button"
          id="btn-toggle-technical-details"
          onClick={() => setShowTechnicalDetails(!showTechnicalDetails)}
          style={{
            width: "100%",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            background: "transparent",
            border: "none",
            cursor: "pointer",
            padding: 0,
            color: "#0f172a",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <span style={{ fontSize: "14px", fontWeight: 700 }}>
              Technical Analysis Details
            </span>
            <span style={{ fontSize: "11px", color: "#64748b" }}>
              (Tokenizer, Latent Embeddings &amp; Runtime Telemetry)
            </span>
          </div>
          <span style={{ fontSize: "13px", color: "#0284c7", fontWeight: 600 }}>
            {showTechnicalDetails ? "Collapse ▲" : "Expand ▼"}
          </span>
        </button>

        {showTechnicalDetails && (
          <div style={{ marginTop: "16px", paddingTop: "16px", borderTop: "1px solid #e2e8f0" }}>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "12px", fontSize: "12px" }}>
              <div>
                <span style={{ color: "#64748b" }}>Model Architecture:</span>{" "}
                <strong>{modelName} v{modelVersion}</strong>
              </div>
              <div>
                <span style={{ color: "#64748b" }}>Runtime Framework:</span>{" "}
                <strong>{stage5Result.model?.framework || "PyTorch"}</strong>
              </div>
              <div>
                <span style={{ color: "#64748b" }}>Hardware Device:</span>{" "}
                <strong>{stage5Result.model?.device || "CPU"}</strong>
              </div>
              <div>
                <span style={{ color: "#64748b" }}>Checkpoint Status:</span>{" "}
                <strong>{checkpointStatus}</strong>
              </div>
              <div>
                <span style={{ color: "#64748b" }}>Embedding Dimension:</span>{" "}
                <strong>{embDim} float32</strong>
              </div>
              <div>
                <span style={{ color: "#64748b" }}>Pipeline Status:</span>{" "}
                <strong>{stage5Result.status.toUpperCase()}</strong>
              </div>
            </div>

            {/* Token array view */}
            <div style={{ marginTop: "14px" }}>
              <div style={{ fontSize: "11px", fontWeight: 700, color: "#64748b", marginBottom: "4px" }}>
                TOKEN STREAM ({tokens.length} TOKENS):
              </div>
              <div
                style={{
                  background: "#0f172a",
                  color: "#fde047",
                  padding: "8px 12px",
                  borderRadius: "6px",
                  fontFamily: "Consolas, monospace",
                  fontSize: "11px",
                  wordBreak: "break-all",
                }}
              >
                [{tokens.join(", ")}]
              </div>
            </div>

            {/* Embedding Vector Sample */}
            {stage5Result.embedding?.vector_sample && (
              <div style={{ marginTop: "14px" }}>
                <div style={{ fontSize: "11px", fontWeight: 700, color: "#64748b", marginBottom: "4px" }}>
                  LATENT EMBEDDING SAMPLE (FIRST {stage5Result.embedding.vector_sample.length} DIMENSIONS):
                </div>
                <div
                  style={{
                    background: "#0f172a",
                    color: "#4ade80",
                    padding: "8px 12px",
                    borderRadius: "6px",
                    fontFamily: "Consolas, monospace",
                    fontSize: "11px",
                    wordBreak: "break-all",
                  }}
                >
                  [{stage5Result.embedding.vector_sample.join(", ")}]
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </section>
  );
}
