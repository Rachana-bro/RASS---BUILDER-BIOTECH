/**
 * RASS-BUILDER: Stage 7 Asynchronous Job Processing & Queue Infrastructure
 * Enables non-blocking background genomic analysis with real-time status polling,
 * stage-based progress visualization, cancellation, and job history.
 */

import React, { useState, useEffect, useRef } from "react";
import {
  createJob,
  getJobStatus,
  cancelJob,
  listJobs,
  type JobDetailResponse,
  type JobSummary,
  type Stage5AnalysisResult,
} from "../services/api";

interface PipelineStage7JobProps {
  currentSequence?: string;
  currentReadId?: string;
  onViewResults?: (result: Stage5AnalysisResult) => void;
}

export const PipelineStage7Job: React.FC<PipelineStage7JobProps> = ({
  currentSequence = "ACGTACGTACGTACGTACGT",
  currentReadId = "READ_001",
  onViewResults,
}) => {
  // Input form state
  const [sequenceInput, setSequenceInput] = useState<string>(currentSequence);
  const [readIdInput, setReadIdInput] = useState<string>(currentReadId);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  // Active job state
  const [activeJob, setActiveJob] = useState<JobDetailResponse | null>(null);
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const [isCancelling, setIsCancelling] = useState<boolean>(false);

  // Job history state
  const [jobHistory, setJobHistory] = useState<JobSummary[]>([]);
  const [historyLoading, setHistoryLoading] = useState<boolean>(false);

  // Polling ref to prevent concurrent / orphaned timers
  const pollTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Synchronize when parent prop changes
  useEffect(() => {
    if (currentSequence) {
      setSequenceInput(currentSequence);
    }
    if (currentReadId) {
      setReadIdInput(currentReadId);
    }
  }, [currentSequence, currentReadId]);

  // Load job history on mount
  useEffect(() => {
    fetchJobHistory();
    return () => stopPolling();
  }, []);

  // Manage polling when activeJobId changes
  useEffect(() => {
    if (!activeJobId) return;

    // Initial fetch
    pollJob(activeJobId);

    // Start interval polling (1.5 seconds)
    stopPolling();
    pollTimerRef.current = setInterval(() => {
      pollJob(activeJobId);
    }, 1500);

    return () => stopPolling();
  }, [activeJobId]);

  function stopPolling() {
    if (pollTimerRef.current) {
      clearInterval(pollTimerRef.current);
      pollTimerRef.current = null;
    }
  }

  async function pollJob(jobId: string) {
    try {
      const jobData = await getJobStatus(jobId);
      setActiveJob(jobData);

      // Stop polling when reached terminal states
      if (
        jobData.status === "COMPLETED" ||
        jobData.status === "FAILED" ||
        jobData.status === "CANCELLED"
      ) {
        stopPolling();
        fetchJobHistory();
      }
    } catch (err: any) {
      // Don't crash UI on occasional polling glitch; stop polling if 404
      if (err.message && err.message.includes("404")) {
        stopPolling();
      }
    }
  }

  async function fetchJobHistory() {
    setHistoryLoading(true);
    try {
      const list = await listJobs(15);
      setJobHistory(list);
    } catch {
      // Graceful fallback for history
    } finally {
      setHistoryLoading(false);
    }
  }

  async function handleSubmitJob(e?: React.FormEvent) {
    if (e) e.preventDefault();
    if (isSubmitting) return; // Prevent duplicate submission

    if (!sequenceInput.trim()) {
      setSubmitError("Please enter or select a valid DNA sequence.");
      return;
    }

    setIsSubmitting(true);
    setSubmitError(null);

    try {
      const response = await createJob({
        sequence: sequenceInput.trim().toUpperCase(),
        read_id: readIdInput.trim() || "READ_001",
        format: "FASTA",
      });

      setActiveJobId(response.job_id);
      fetchJobHistory();
    } catch (err: any) {
      setSubmitError(err.message || "Failed to enqueue analysis job.");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleCancelJob() {
    if (!activeJobId || isCancelling) return;
    setIsCancelling(true);
    try {
      const updated = await cancelJob(activeJobId);
      setActiveJob(updated);
      stopPolling();
      fetchJobHistory();
    } catch (err: any) {
      alert(`Could not cancel job: ${err.message}`);
    } finally {
      setIsCancelling(false);
    }
  }

  function handleSelectHistoryJob(jobId: string) {
    setActiveJobId(jobId);
  }

  function handleViewResults() {
    if (!activeJob?.result_reference) return;
    if (onViewResults) {
      onViewResults(activeJob.result_reference);
    }
    // Scroll smoothly to Stage 6 Results section
    const stage6Elem = document.getElementById("stage6-results-container");
    if (stage6Elem) {
      stage6Elem.scrollIntoView({ behavior: "smooth" });
    }
  }

  // Format stage display names
  function formatStage(stage: string): string {
    switch (stage) {
      case "QUEUED":
        return "Queued in Pipeline";
      case "DATA_INGESTION":
        return "Data Ingestion & Ingestion Validation";
      case "QUALITY_CONTROL":
        return "Stage 4 QC & Read Filtering";
      case "TRANSFORMER_ANALYSIS":
        return "Stage 5 DNA Transformer Embedding";
      case "PATTERN_ANALYSIS":
        return "Multi-Head Attention & Pattern Checkpoint";
      case "COMPLETED":
        return "Analysis Pipeline Completed";
      case "FAILED":
        return "Pipeline Failed";
      case "CANCELLED":
        return "Execution Cancelled";
      case "RECOVERY_REQUIRED":
        return "Interrupted by Server Restart — Recovery Required";
      default:
        return stage;
    }
  }

  // Status badge color tokens
  function getStatusBadgeStyle(status: string) {
    switch (status) {
      case "QUEUED":
        return {
          bg: "rgba(245, 158, 11, 0.15)",
          border: "#f59e0b",
          color: "#fbbf24",
          text: "QUEUED",
        };
      case "RUNNING":
        return {
          bg: "rgba(56, 189, 248, 0.15)",
          border: "#38bdf8",
          color: "#38bdf8",
          text: "RUNNING",
        };
      case "COMPLETED":
        return {
          bg: "rgba(16, 185, 129, 0.15)",
          border: "#10b981",
          color: "#34d399",
          text: "COMPLETED",
        };
      case "FAILED":
        return {
          bg: "rgba(239, 68, 68, 0.15)",
          border: "#ef4444",
          color: "#f87171",
          text: "FAILED",
        };
      case "CANCELLED":
        return {
          bg: "rgba(100, 116, 139, 0.15)",
          border: "#64748b",
          color: "#94a3b8",
          text: "CANCELLED",
        };
      case "RECOVERY_REQUIRED":
        return {
          bg: "rgba(249, 115, 22, 0.15)",
          border: "#f97316",
          color: "#fb923c",
          text: "RECOVERY REQUIRED",
        };
      default:
        return {
          bg: "rgba(148, 163, 184, 0.15)",
          border: "#94a3b8",
          color: "#cbd5e1",
          text: status,
        };
    }
  }

  return (
    <section
      id="stage7-jobs-container"
      style={{
        marginTop: "32px",
        background: "#0b1120",
        border: "1px solid #1e293b",
        borderRadius: "14px",
        padding: "30px",
        color: "#f8fafc",
        fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
      }}
    >
      {/* HEADER BAR */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          borderBottom: "1px solid #1e293b",
          paddingBottom: "20px",
          marginBottom: "26px",
          flexWrap: "wrap",
          gap: "14px",
        }}
      >
        <div>
          <div
            style={{
              display: "inline-block",
              padding: "4px 10px",
              background: "rgba(56, 189, 248, 0.12)",
              border: "1px solid #0284c7",
              borderRadius: "6px",
              fontSize: "11px",
              fontWeight: 800,
              letterSpacing: "0.08em",
              color: "#38bdf8",
              marginBottom: "8px",
            }}
          >
            STAGE 7 — ASYNCHRONOUS JOB PIPELINE & QUEUE
          </div>
          <h2
            style={{
              margin: 0,
              fontSize: "22px",
              fontWeight: 700,
              color: "#f1f5f9",
            }}
          >
            Background Genomic Analysis Worker
          </h2>
          <p
            style={{
              margin: "6px 0 0",
              fontSize: "13px",
              color: "#94a3b8",
              maxWidth: "760px",
            }}
          >
            Dispatches sequence analysis to the background queue. Non-blocking
            execution routes through Stage 4 Quality Control, Stage 5 DNA
            Transformer, and emits structured results directly into Stage 6.
          </p>
        </div>

        <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
          <button
            type="button"
            onClick={fetchJobHistory}
            disabled={historyLoading}
            style={{
              padding: "7px 14px",
              background: "#1e293b",
              border: "1px solid #334155",
              borderRadius: "7px",
              color: "#cbd5e1",
              fontSize: "12px",
              fontWeight: 600,
              cursor: historyLoading ? "not-allowed" : "pointer",
            }}
          >
            {historyLoading ? "Refreshing..." : "↻ Refresh History"}
          </button>
        </div>
      </div>

      {/* SUBMISSION FORM */}
      <div
        style={{
          background: "#0f172a",
          border: "1px solid #1e293b",
          borderRadius: "10px",
          padding: "20px",
          marginBottom: "26px",
        }}
      >
        <h3
          style={{
            margin: "0 0 14px 0",
            fontSize: "15px",
            fontWeight: 700,
            color: "#e2e8f0",
          }}
        >
          Enqueue Analysis Job
        </h3>

        <form onSubmit={handleSubmitJob}>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 220px",
              gap: "16px",
              marginBottom: "14px",
            }}
          >
            <div>
              <label
                style={{
                  display: "block",
                  fontSize: "12px",
                  fontWeight: 600,
                  color: "#94a3b8",
                  marginBottom: "6px",
                }}
              >
                DNA Sequence (A, C, G, T, N)
              </label>
              <textarea
                value={sequenceInput}
                onChange={(e) => setSequenceInput(e.target.value)}
                placeholder="Paste DNA sequence for asynchronous analysis..."
                rows={3}
                style={{
                  width: "100%",
                  boxSizing: "border-box",
                  background: "#020617",
                  border: "1px solid #334155",
                  borderRadius: "7px",
                  padding: "10px 12px",
                  color: "#e2e8f0",
                  fontFamily: "monospace",
                  fontSize: "12px",
                  resize: "vertical",
                }}
              />
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  fontSize: "11px",
                  color: "#64748b",
                  marginTop: "4px",
                }}
              >
                <span>Length: {sequenceInput.trim().length} bp</span>
                <button
                  type="button"
                  onClick={() => {
                    setSequenceInput(currentSequence);
                    setReadIdInput(currentReadId);
                  }}
                  style={{
                    background: "none",
                    border: "none",
                    color: "#38bdf8",
                    cursor: "pointer",
                    fontSize: "11px",
                    padding: 0,
                    textDecoration: "underline",
                  }}
                >
                  Load from Stage 4/5 Selection
                </button>
              </div>
            </div>

            <div>
              <label
                style={{
                  display: "block",
                  fontSize: "12px",
                  fontWeight: 600,
                  color: "#94a3b8",
                  marginBottom: "6px",
                }}
              >
                Read Identifier
              </label>
              <input
                type="text"
                value={readIdInput}
                onChange={(e) => setReadIdInput(e.target.value)}
                placeholder="READ_001"
                style={{
                  width: "100%",
                  boxSizing: "border-box",
                  background: "#020617",
                  border: "1px solid #334155",
                  borderRadius: "7px",
                  padding: "10px 12px",
                  color: "#e2e8f0",
                  fontSize: "12px",
                  marginBottom: "12px",
                }}
              />

              <button
                id="btn-submit-async-job"
                type="submit"
                disabled={isSubmitting || !sequenceInput.trim()}
                style={{
                  width: "100%",
                  padding: "11px 16px",
                  background: isSubmitting ? "#0284c7" : "#0ea5e9",
                  border: "none",
                  borderRadius: "7px",
                  color: "#ffffff",
                  fontSize: "13px",
                  fontWeight: 700,
                  cursor: isSubmitting || !sequenceInput.trim() ? "not-allowed" : "pointer",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  gap: "8px",
                  boxShadow: "0 2px 8px rgba(14, 165, 233, 0.3)",
                }}
              >
                {isSubmitting ? (
                  <>
                    <span
                      style={{
                        display: "inline-block",
                        width: "12px",
                        height: "12px",
                        border: "2px solid #ffffff",
                        borderTopColor: "transparent",
                        borderRadius: "50%",
                        animation: "spin 0.8s linear infinite",
                      }}
                    />
                    Queueing Job...
                  </>
                ) : (
                  <>🚀 Submit Asynchronous Analysis</>
                )}
              </button>
            </div>
          </div>

          {submitError && (
            <div
              style={{
                padding: "8px 12px",
                background: "rgba(239, 68, 68, 0.15)",
                border: "1px solid #ef4444",
                borderRadius: "6px",
                color: "#fca5a5",
                fontSize: "12px",
              }}
            >
              ⚠ {submitError}
            </div>
          )}
        </form>
      </div>

      {/* ACTIVE JOB MONITOR */}
      {activeJob && (
        <div
          style={{
            background: "#0f172a",
            border: "1px solid #1e293b",
            borderRadius: "10px",
            padding: "22px",
            marginBottom: "26px",
          }}
        >
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginBottom: "16px",
              flexWrap: "wrap",
              gap: "10px",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <span
                style={{
                  fontSize: "11px",
                  color: "#94a3b8",
                  letterSpacing: "0.06em",
                  fontWeight: 700,
                }}
              >
                ACTIVE ANALYSIS JOB:
              </span>
              <span
                style={{
                  fontSize: "15px",
                  fontFamily: "monospace",
                  fontWeight: 800,
                  color: "#38bdf8",
                  background: "rgba(56, 189, 248, 0.1)",
                  padding: "3px 8px",
                  borderRadius: "5px",
                  border: "1px solid #0284c7",
                }}
              >
                {activeJob.job_id}
              </span>
              <button
                type="button"
                onClick={() => navigator.clipboard.writeText(activeJob.job_id)}
                title="Copy Job ID"
                style={{
                  background: "none",
                  border: "none",
                  color: "#64748b",
                  cursor: "pointer",
                  fontSize: "12px",
                  padding: "2px 4px",
                }}
              >
                📋
              </button>
            </div>

            {/* STATUS BADGE */}
            {(() => {
              const badge = getStatusBadgeStyle(activeJob.status);
              return (
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "8px",
                    padding: "6px 14px",
                    background: badge.bg,
                    border: `1px solid ${badge.border}`,
                    borderRadius: "20px",
                    color: badge.color,
                    fontSize: "12px",
                    fontWeight: 800,
                  }}
                >
                  {activeJob.status === "RUNNING" && (
                    <span
                      style={{
                        width: "8px",
                        height: "8px",
                        borderRadius: "50%",
                        background: "#38bdf8",
                        display: "inline-block",
                        animation: "pulse 1.2s infinite",
                      }}
                    />
                  )}
                  {badge.text}
                </div>
              );
            })()}
          </div>

          {/* PROGRESS BAR */}
          <div style={{ marginBottom: "16px" }}>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                fontSize: "12px",
                marginBottom: "6px",
              }}
            >
              <span style={{ color: "#cbd5e1", fontWeight: 600 }}>
                {formatStage(activeJob.current_stage)}
              </span>
              <span
                style={{
                  color: "#38bdf8",
                  fontWeight: 800,
                  fontFamily: "monospace",
                }}
              >
                {activeJob.progress}%
              </span>
            </div>

            <div
              style={{
                width: "100%",
                height: "10px",
                background: "#020617",
                borderRadius: "5px",
                overflow: "hidden",
                border: "1px solid #1e293b",
              }}
            >
              <div
                style={{
                  width: `${activeJob.progress}%`,
                  height: "100%",
                  background:
                    activeJob.status === "FAILED"
                      ? "#ef4444"
                      : activeJob.status === "COMPLETED"
                      ? "#10b981"
                      : "linear-gradient(90deg, #0284c7 0%, #38bdf8 100%)",
                  borderRadius: "5px",
                  transition: "width 0.4s ease-out",
                }}
              />
            </div>
          </div>

          {/* LIVE STATUS MESSAGE */}
          <div
            style={{
              padding: "10px 14px",
              background: "#020617",
              border: "1px solid #1e293b",
              borderRadius: "7px",
              fontSize: "12px",
              color: "#94a3b8",
              marginBottom: "16px",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              flexWrap: "wrap",
              gap: "8px",
            }}
          >
            <span>
              <strong style={{ color: "#cbd5e1" }}>Status Message:</strong>{" "}
              {activeJob.message}
            </span>
            <span style={{ fontSize: "11px", color: "#64748b" }}>
              Created: {new Date(activeJob.created_at).toLocaleTimeString()}
            </span>
          </div>

          {/* COMPLETED ACTIONS */}
          {activeJob.status === "COMPLETED" && (
            <div
              style={{
                padding: "16px",
                background: "rgba(16, 185, 129, 0.12)",
                border: "1px solid #10b981",
                borderRadius: "8px",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                flexWrap: "wrap",
                gap: "12px",
              }}
            >
              <div>
                <div
                  style={{
                    fontSize: "14px",
                    fontWeight: 700,
                    color: "#34d399",
                    marginBottom: "4px",
                  }}
                >
                  ✓ ANALYSIS COMPLETED
                </div>
                <div style={{ fontSize: "12px", color: "#a7f3d0" }}>
                  Genomic pipeline executed successfully through Stages 4 and 5.
                  Structured result object is ready for laboratory inspection.
                </div>
              </div>

              <button
                id="btn-view-job-results"
                type="button"
                onClick={handleViewResults}
                style={{
                  padding: "9px 18px",
                  background: "#10b981",
                  border: "none",
                  borderRadius: "7px",
                  color: "#064e3b",
                  fontSize: "13px",
                  fontWeight: 800,
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  gap: "6px",
                  boxShadow: "0 2px 8px rgba(16, 185, 129, 0.4)",
                }}
              >
                🔬 View Results in Stage 6 Dashboard ↓
              </button>
            </div>
          )}

          {/* FAILED ACTIONS */}
          {activeJob.status === "FAILED" && (
            <div
              style={{
                padding: "16px",
                background: "rgba(239, 68, 68, 0.12)",
                border: "1px solid #ef4444",
                borderRadius: "8px",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                flexWrap: "wrap",
                gap: "12px",
              }}
            >
              <div>
                <div
                  style={{
                    fontSize: "14px",
                    fontWeight: 700,
                    color: "#f87171",
                    marginBottom: "4px",
                  }}
                >
                  ✕ ANALYSIS FAILED
                </div>
                <div style={{ fontSize: "12px", color: "#fca5a5" }}>
                  {activeJob.error ||
                    "Analysis could not be completed. Please review the input data and try again."}
                </div>
              </div>

              <button
                type="button"
                onClick={() => handleSubmitJob()}
                style={{
                  padding: "8px 16px",
                  background: "#ef4444",
                  border: "none",
                  borderRadius: "7px",
                  color: "#ffffff",
                  fontSize: "12px",
                  fontWeight: 700,
                  cursor: "pointer",
                }}
              >
                ↻ Retry Analysis
              </button>
            </div>
          )}

          {/* CANCEL BUTTON FOR ACTIVE/QUEUED JOBS */}
          {(activeJob.status === "QUEUED" || activeJob.status === "RUNNING") && (
            <div style={{ display: "flex", justifyContent: "flex-end" }}>
              <button
                id="btn-cancel-job"
                type="button"
                onClick={handleCancelJob}
                disabled={isCancelling}
                style={{
                  padding: "7px 14px",
                  background: "transparent",
                  border: "1px solid #64748b",
                  borderRadius: "6px",
                  color: "#94a3b8",
                  fontSize: "12px",
                  fontWeight: 600,
                  cursor: isCancelling ? "not-allowed" : "pointer",
                }}
              >
                {isCancelling ? "Cancelling..." : "Cancel Job"}
              </button>
            </div>
          )}
        </div>
      )}

      {/* JOB HISTORY TABLE */}
      <div>
        <h3
          style={{
            margin: "0 0 12px 0",
            fontSize: "14px",
            fontWeight: 700,
            color: "#cbd5e1",
          }}
        >
          Recent Job History
        </h3>

        {jobHistory.length === 0 ? (
          <div
            style={{
              padding: "20px",
              background: "#0f172a",
              border: "1px solid #1e293b",
              borderRadius: "8px",
              textAlign: "center",
              fontSize: "12px",
              color: "#64748b",
            }}
          >
            No background analysis jobs registered yet. Submit a sequence above to initiate a job.
          </div>
        ) : (
          <div
            style={{
              overflowX: "auto",
              border: "1px solid #1e293b",
              borderRadius: "8px",
              background: "#0f172a",
            }}
          >
            <table
              style={{
                width: "100%",
                borderCollapse: "collapse",
                fontSize: "12px",
                textAlign: "left",
              }}
            >
              <thead>
                <tr
                  style={{
                    background: "#020617",
                    borderBottom: "1px solid #1e293b",
                    color: "#94a3b8",
                  }}
                >
                  <th style={{ padding: "10px 14px", fontWeight: 600 }}>Job ID</th>
                  <th style={{ padding: "10px 14px", fontWeight: 600 }}>Created</th>
                  <th style={{ padding: "10px 14px", fontWeight: 600 }}>Target</th>
                  <th style={{ padding: "10px 14px", fontWeight: 600 }}>Status</th>
                  <th style={{ padding: "10px 14px", fontWeight: 600 }}>Progress</th>
                  <th style={{ padding: "10px 14px", fontWeight: 600, textAlign: "right" }}>
                    Action
                  </th>
                </tr>
              </thead>
              <tbody>
                {jobHistory.map((item) => {
                  const badge = getStatusBadgeStyle(item.status);
                  const isCurrent = activeJob?.job_id === item.job_id;
                  return (
                    <tr
                      key={item.job_id}
                      style={{
                        borderBottom: "1px solid #1e293b",
                        background: isCurrent ? "rgba(56, 189, 248, 0.05)" : "transparent",
                      }}
                    >
                      <td
                        style={{
                          padding: "10px 14px",
                          fontFamily: "monospace",
                          fontWeight: 700,
                          color: "#38bdf8",
                        }}
                      >
                        {item.job_id}
                      </td>
                      <td style={{ padding: "10px 14px", color: "#94a3b8" }}>
                        {new Date(item.created_at).toLocaleTimeString()}
                      </td>
                      <td style={{ padding: "10px 14px", color: "#cbd5e1" }}>
                        {item.read_id || "READ_001"} ({item.sequence_length || 0} bp)
                      </td>
                      <td style={{ padding: "10px 14px" }}>
                        <span
                          style={{
                            padding: "3px 8px",
                            borderRadius: "12px",
                            fontSize: "11px",
                            fontWeight: 700,
                            background: badge.bg,
                            border: `1px solid ${badge.border}`,
                            color: badge.color,
                          }}
                        >
                          {badge.text}
                        </span>
                      </td>
                      <td
                        style={{
                          padding: "10px 14px",
                          fontFamily: "monospace",
                          color: "#cbd5e1",
                        }}
                      >
                        {item.progress}%
                      </td>
                      <td
                        style={{
                          padding: "10px 14px",
                          textAlign: "right",
                        }}
                      >
                        <button
                          type="button"
                          onClick={() => handleSelectHistoryJob(item.job_id)}
                          style={{
                            padding: "4px 10px",
                            background: isCurrent ? "#0284c7" : "#1e293b",
                            border: "1px solid #334155",
                            borderRadius: "5px",
                            color: isCurrent ? "#ffffff" : "#cbd5e1",
                            fontSize: "11px",
                            fontWeight: 600,
                            cursor: "pointer",
                          }}
                        >
                          {item.status === "COMPLETED" ? "View Results" : "Inspect Status"}
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* FOOTER NOTICE */}
      <div
        style={{
          marginTop: "20px",
          padding: "10px 14px",
          background: "rgba(15, 23, 42, 0.6)",
          border: "1px solid #1e293b",
          borderRadius: "6px",
          fontSize: "11px",
          color: "#64748b",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <span>
          🛡 <strong>Persistence Architecture:</strong> Persistent SQLite Database &amp; WAL Mode (Stage 8).
          Job lifecycle and structured analysis results are retained across backend restarts.
        </span>
        <span>Zero-mutation fabrication in effect.</span>
      </div>
    </section>
  );
};

export default PipelineStage7Job;
