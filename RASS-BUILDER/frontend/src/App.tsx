import { useState, useEffect } from "react";

import FastqUpload from "./components/FastqUpload";
import QcDashboard from "./components/QcDashboard";
import PipelineStage4 from "./components/PipelineStage4";
import PipelineStage5 from "./components/PipelineStage5";
import PipelineStage6 from "./components/PipelineStage6";
import PipelineStage7Job from "./components/PipelineStage7Job";
import AuthModal from "./components/AuthModal";
import { getMe, logout, getStoredToken } from "./services/auth";
import type { Stage5Result } from "./services/api";
import type { User } from "./types/auth";


function App() {
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [authModalOpen, setAuthModalOpen] = useState<boolean>(false);
  const [isInitializingAuth, setIsInitializingAuth] = useState<boolean>(true);

  const [result, setResult] =
    useState<any>(null);

  const [stage5Sequence, setStage5Sequence] =
    useState<string>("ACGTACGTACGTACGTACGT");

  const [stage5ReadId, setStage5ReadId] =
    useState<string>("READ_001");

  const [stage5AnalysisResult, setStage5AnalysisResult] =
    useState<Stage5Result | null>(null);

  useEffect(() => {
    async function checkActiveSession() {
      const token = getStoredToken();
      if (token) {
        try {
          const user = await getMe();
          setCurrentUser(user);
        } catch {
          setCurrentUser(null);
          setAuthModalOpen(true);
        }
      } else {
        setAuthModalOpen(true);
      }
      setIsInitializingAuth(false);
    }
    checkActiveSession();
  }, []);

  function handleSelectReadForStage5(seq: string, readId: string) {
    setStage5Sequence(seq);
    setStage5ReadId(readId);
  }

  function handleStage5DemoTrigger() {
    const stage5RunBtn = document.getElementById("btn-run-stage5");
    if (stage5RunBtn) {
      stage5RunBtn.click();
    }
  }

  async function handleLogout() {
    await logout();
    setCurrentUser(null);
    setAuthModalOpen(true);
  }

  return (
    <main
      style={{
        minHeight: "100vh",
        background: "#f8fafc",
        color: "#0f172a",
        fontFamily:
          "Inter, Arial, sans-serif",
      }}
    >

      {/* TOP BAR */}
      <header
        style={{
          background: "#ffffff",
          borderBottom:
            "1px solid #e2e8f0",
          padding:
            "18px 40px",
        }}
      >

        <div
          style={{
            maxWidth: "1200px",
            margin: "0 auto",
            display: "flex",
            justifyContent:
              "space-between",
            alignItems: "center",
            gap: "16px",
            flexWrap: "wrap",
          }}
        >

          <div>
            <div
              style={{
                fontSize: "18px",
                fontWeight: 800,
              }}
            >
              RASS-BUILDER
            </div>

            <div
              style={{
                fontSize: "11px",
                color: "#64748b",
                letterSpacing:
                  "0.08em",
              }}
            >
              SEQUENCING ANALYSIS WORKSTATION
            </div>
          </div>


          {/* STATUS PILLS & AUTH STATE */}
          <div style={{ display: "flex", gap: "8px", alignItems: "center", flexWrap: "wrap" }}>
            <div
              style={{
                padding: "6px 12px",
                border: "1px solid #fbcfe8",
                borderRadius: "20px",
                color: "#be185d",
                background: "#fdf2f8",
                fontSize: "11px",
                fontWeight: 700,
              }}
            >
              STAGE 9 AUTH & RBAC
            </div>

            <div
              style={{
                padding: "6px 12px",
                border: "1px solid #a7f3d0",
                borderRadius: "20px",
                color: "#047857",
                background: "#ecfdf5",
                fontSize: "11px",
                fontWeight: 700,
              }}
            >
              STAGE 8 PERSISTENT DB
            </div>

            <div
              style={{
                padding: "6px 12px",
                border: "1px solid #7dd3fc",
                borderRadius: "20px",
                color: "#0369a1",
                background: "#f0f9ff",
                fontSize: "11px",
                fontWeight: 700,
              }}
            >
              STAGE 7 ASYNC QUEUE
            </div>

            <div
              style={{
                padding: "6px 12px",
                border: "1px solid #bae6fd",
                borderRadius: "20px",
                color: "#0284c7",
                background: "#f0f9ff",
                fontSize: "11px",
                fontWeight: 700,
              }}
            >
              STAGE 6 RESULTS
            </div>

            <div
              style={{
                padding: "6px 12px",
                border: "1px solid #ddd6fe",
                borderRadius: "20px",
                color: "#6d28d9",
                background: "#f5f3ff",
                fontSize: "11px",
                fontWeight: 700,
              }}
            >
              STAGE 5 AI LAYER
            </div>

            {/* USER / SESSION ACCOUNT PILL */}
            {currentUser ? (
              <div
                id="header-user-badge"
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "8px",
                  padding: "4px 10px 4px 12px",
                  background: "#f8fafc",
                  border: "1px solid #cbd5e1",
                  borderRadius: "20px",
                  fontSize: "12px",
                }}
              >
                <span style={{ fontWeight: 600, color: "#1e293b" }}>
                  {currentUser.name}
                </span>
                <span
                  style={{
                    fontSize: "10px",
                    fontWeight: 700,
                    padding: "2px 6px",
                    borderRadius: "10px",
                    color: currentUser.role === "ADMIN" ? "#b45309" : "#0284c7",
                    background: currentUser.role === "ADMIN" ? "#fef3c7" : "#e0f2fe",
                    border: currentUser.role === "ADMIN" ? "1px solid #fde68a" : "1px solid #bae6fd",
                  }}
                >
                  {currentUser.role}
                </span>
                <button
                  type="button"
                  id="btn-header-logout"
                  onClick={handleLogout}
                  style={{
                    background: "transparent",
                    border: "none",
                    color: "#64748b",
                    fontSize: "11px",
                    fontWeight: 600,
                    cursor: "pointer",
                    padding: "2px 4px",
                    marginLeft: "2px",
                    textDecoration: "underline",
                  }}
                >
                  Logout
                </button>
              </div>
            ) : (
              <button
                type="button"
                id="btn-header-login"
                onClick={() => setAuthModalOpen(true)}
                style={{
                  padding: "6px 14px",
                  background: "#2563eb",
                  color: "#ffffff",
                  border: "none",
                  borderRadius: "20px",
                  fontSize: "12px",
                  fontWeight: 700,
                  cursor: "pointer",
                }}
              >
                Sign In
              </button>
            )}
          </div>

        </div>

      </header>

      {/* AUTHENTICATION MODAL */}
      <AuthModal
        isOpen={authModalOpen}
        onSuccess={(user) => {
          setCurrentUser(user);
          setAuthModalOpen(false);
        }}
        onClose={currentUser ? () => setAuthModalOpen(false) : undefined}
      />

      {/* MAIN WORKSTATION CONTENT */}
      <div
        style={{
          maxWidth: "1200px",
          margin: "0 auto",
          padding: "40px 24px 80px",
        }}
      >
        {!currentUser && !isInitializingAuth ? (
          <div
            id="auth-gate-banner"
            style={{
              background: "#ffffff",
              border: "1px solid #e2e8f0",
              borderRadius: "12px",
              padding: "48px 32px",
              textAlign: "center",
              boxShadow: "0 1px 3px rgba(0,0,0,0.05)",
            }}
          >
            <div
              style={{
                display: "inline-block",
                padding: "8px 16px",
                background: "#eff6ff",
                border: "1px solid #bfdbfe",
                borderRadius: "20px",
                color: "#1d4999",
                fontSize: "12px",
                fontWeight: 700,
                marginBottom: "16px",
              }}
            >
              AUTHENTICATION REQUIRED
            </div>
            <h2 style={{ fontSize: "24px", fontWeight: 800, margin: "0 0 12px", color: "#0f172a" }}>
              Workstation Protected by Role-Based Access Control
            </h2>
            <p style={{ color: "#64748b", maxWidth: "600px", margin: "0 auto 24px", fontSize: "14px", lineHeight: "1.5" }}>
              Sign in with your researcher credentials or create a secure account to access genomic FASTQ quality control,
              DNA Transformer tokenization, asynchronous analysis queues, and persistent results.
            </p>
            <button
              type="button"
              id="btn-gate-signin"
              onClick={() => setAuthModalOpen(true)}
              style={{
                padding: "12px 28px",
                background: "#2563eb",
                color: "#ffffff",
                border: "none",
                borderRadius: "8px",
                fontSize: "14px",
                fontWeight: 700,
                cursor: "pointer",
                boxShadow: "0 4px 6px -1px rgba(37, 99, 235, 0.2)",
              }}
            >
              Sign In to Workstation
            </button>
          </div>
        ) : (
          <>
            <section
              style={{
                background: "#ffffff",
                border:
                  "1px solid #e2e8f0",
                borderRadius: "12px",
                padding: "28px",
              }}
            >

              <h1
                style={{
                  marginTop: 0,
                  fontSize: "30px",
                }}
              >
                Sequencing Analysis
              </h1>

              <p
                style={{
                  color: "#64748b",
                  maxWidth: "700px",
                }}
              >
                Upload a FASTQ dataset to perform
                sequencing quality control and
                generate per-cycle quality metrics.
              </p>

              <FastqUpload
                onComplete={setResult}
              />

            </section>


            <QcDashboard
              result={result}
            />

            <PipelineStage4
              onSelectSequenceForStage5={handleSelectReadForStage5}
            />

            <PipelineStage5
              key={`${stage5ReadId}-${stage5Sequence.substring(0, 10)}`}
              initialSequence={stage5Sequence}
              initialReadId={stage5ReadId}
              onAnalysisComplete={setStage5AnalysisResult}
            />

            <PipelineStage7Job
              currentSequence={stage5Sequence}
              currentReadId={stage5ReadId}
              onViewResults={setStage5AnalysisResult}
            />

            <PipelineStage6
              stage5Result={stage5AnalysisResult}
              onTriggerStage5Demo={handleStage5DemoTrigger}
            />
          </>
        )}
      </div>

    </main>
  );
}


export default App;
