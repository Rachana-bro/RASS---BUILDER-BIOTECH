import React, { useState } from "react";
import { login, register } from "../services/auth";
import type { User } from "../types/auth";

interface AuthModalProps {
  onSuccess: (user: User) => void;
  isOpen: boolean;
  onClose?: () => void;
}

export default function AuthModal({ onSuccess, isOpen, onClose }: AuthModalProps) {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [role, setRole] = useState<"USER" | "ADMIN">("USER");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      if (mode === "login") {
        if (!email.trim() || !password) {
          setError("Please enter your email/username and password.");
          setLoading(false);
          return;
        }
        const resp = await login(email.trim(), password);
        onSuccess(resp.user);
      } else {
        if (!name.trim()) {
          setError("Name is required.");
          setLoading(false);
          return;
        }
        if (!email.trim()) {
          setError("Email or username is required.");
          setLoading(false);
          return;
        }
        if (password.length < 8) {
          setError("Password must be at least 8 characters long.");
          setLoading(false);
          return;
        }
        if (password !== confirmPassword) {
          setError("Passwords do not match.");
          setLoading(false);
          return;
        }
        const resp = await register(
          name.trim(),
          email.trim(),
          password,
          confirmPassword,
          role
        );
        onSuccess(resp.user);
      }
    } catch (err: any) {
      setError(err.message || "Authentication failed. Please verify credentials.");
    } finally {
      setLoading(false);
    }
  }

  function handleDemoFill(demoRole: "USER" | "ADMIN") {
    setError(null);
    if (demoRole === "ADMIN") {
      setMode("register");
      setName("Admin Director");
      setEmail("admin@biolab.org");
      setPassword("AdminSecure2026!");
      setConfirmPassword("AdminSecure2026!");
      setRole("ADMIN");
    } else {
      setMode("register");
      setName("Genomics Researcher");
      setEmail("researcher@biolab.org");
      setPassword("ResearchPass2026!");
      setConfirmPassword("ResearchPass2026!");
      setRole("USER");
    }
  }

  return (
    <div
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: "rgba(15, 23, 42, 0.75)",
        backdropFilter: "blur(4px)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 9999,
        padding: "16px",
      }}
    >
      <div
        style={{
          width: "100%",
          maxWidth: "440px",
          background: "#ffffff",
          borderRadius: "12px",
          border: "1px solid #e2e8f0",
          boxShadow: "0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1)",
          overflow: "hidden",
        }}
      >
        {/* Header */}
        <div
          style={{
            padding: "24px 28px 16px",
            borderBottom: "1px solid #f1f5f9",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div>
              <div style={{ fontSize: "18px", fontWeight: 800, color: "#0f172a", letterSpacing: "-0.01em" }}>
                RASS-BUILDER
              </div>
              <div style={{ fontSize: "11px", color: "#64748b", fontWeight: 600, letterSpacing: "0.06em", textTransform: "uppercase", marginTop: "2px" }}>
                Workstation Access Control
              </div>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <div
                style={{
                  fontSize: "11px",
                  fontWeight: 700,
                  color: "#2563eb",
                  background: "#eff6ff",
                  border: "1px solid #bfdbfe",
                  padding: "3px 8px",
                  borderRadius: "12px",
                }}
              >
                STAGE 9 SECURE
              </div>
              {onClose && (
                <button
                  type="button"
                  id="btn-auth-close"
                  onClick={onClose}
                  style={{
                    background: "transparent",
                    border: "none",
                    color: "#64748b",
                    fontSize: "16px",
                    cursor: "pointer",
                    padding: "2px 6px",
                  }}
                  title="Close"
                >
                  ✕
                </button>
              )}
            </div>
          </div>


          {/* Mode Switch Tabs */}
          <div
            style={{
              display: "flex",
              gap: "4px",
              marginTop: "18px",
              background: "#f1f5f9",
              padding: "3px",
              borderRadius: "8px",
            }}
          >
            <button
              type="button"
              id="tab-auth-login"
              onClick={() => {
                setMode("login");
                setError(null);
              }}
              style={{
                flex: 1,
                padding: "8px 12px",
                fontSize: "13px",
                fontWeight: mode === "login" ? 700 : 500,
                color: mode === "login" ? "#0f172a" : "#64748b",
                background: mode === "login" ? "#ffffff" : "transparent",
                border: "none",
                borderRadius: "6px",
                cursor: "pointer",
                boxShadow: mode === "login" ? "0 1px 3px rgba(0,0,0,0.1)" : "none",
                transition: "all 0.15s ease",
              }}
            >
              Sign In
            </button>
            <button
              type="button"
              id="tab-auth-register"
              onClick={() => {
                setMode("register");
                setError(null);
              }}
              style={{
                flex: 1,
                padding: "8px 12px",
                fontSize: "13px",
                fontWeight: mode === "register" ? 700 : 500,
                color: mode === "register" ? "#0f172a" : "#64748b",
                background: mode === "register" ? "#ffffff" : "transparent",
                border: "none",
                borderRadius: "6px",
                cursor: "pointer",
                boxShadow: mode === "register" ? "0 1px 3px rgba(0,0,0,0.1)" : "none",
                transition: "all 0.15s ease",
              }}
            >
              Create Account
            </button>
          </div>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} style={{ padding: "20px 28px 24px" }}>
          {error && (
            <div
              id="auth-error-banner"
              style={{
                marginBottom: "16px",
                padding: "10px 14px",
                backgroundColor: "#fef2f2",
                border: "1px solid #fecaca",
                borderRadius: "6px",
                fontSize: "12px",
                color: "#b91c1c",
                lineHeight: "1.4",
              }}
            >
              {error}
            </div>
          )}

          {mode === "register" && (
            <div style={{ marginBottom: "14px" }}>
              <label
                htmlFor="auth-name"
                style={{ display: "block", fontSize: "12px", fontWeight: 600, color: "#334155", marginBottom: "5px" }}
              >
                Full Name
              </label>
              <input
                id="auth-name"
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Dr. Jane Doe"
                style={{
                  width: "100%",
                  padding: "9px 12px",
                  fontSize: "13px",
                  borderRadius: "6px",
                  border: "1px solid #cbd5e1",
                  outline: "none",
                  boxSizing: "border-box",
                }}
              />
            </div>
          )}

          <div style={{ marginBottom: "14px" }}>
            <label
              htmlFor="auth-email"
              style={{ display: "block", fontSize: "12px", fontWeight: 600, color: "#334155", marginBottom: "5px" }}
            >
              Email or Username
            </label>
            <input
              id="auth-email"
              type="text"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="user@biolab.org"
              style={{
                width: "100%",
                padding: "9px 12px",
                fontSize: "13px",
                borderRadius: "6px",
                border: "1px solid #cbd5e1",
                outline: "none",
                boxSizing: "border-box",
              }}
            />
          </div>

          <div style={{ marginBottom: "14px" }}>
            <label
              htmlFor="auth-password"
              style={{ display: "block", fontSize: "12px", fontWeight: 600, color: "#334155", marginBottom: "5px" }}
            >
              Password
            </label>
            <input
              id="auth-password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••••••"
              style={{
                width: "100%",
                padding: "9px 12px",
                fontSize: "13px",
                borderRadius: "6px",
                border: "1px solid #cbd5e1",
                outline: "none",
                boxSizing: "border-box",
              }}
            />
            {mode === "register" && (
              <div style={{ fontSize: "11px", color: "#64748b", marginTop: "4px" }}>
                Min 8 characters, at least 1 letter and 1 number or symbol
              </div>
            )}
          </div>

          {mode === "register" && (
            <>
              <div style={{ marginBottom: "14px" }}>
                <label
                  htmlFor="auth-confirm-password"
                  style={{ display: "block", fontSize: "12px", fontWeight: 600, color: "#334155", marginBottom: "5px" }}
                >
                  Confirm Password
                </label>
                <input
                  id="auth-confirm-password"
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="••••••••••••"
                  style={{
                    width: "100%",
                    padding: "9px 12px",
                    fontSize: "13px",
                    borderRadius: "6px",
                    border: "1px solid #cbd5e1",
                    outline: "none",
                    boxSizing: "border-box",
                  }}
                />
              </div>

              <div style={{ marginBottom: "18px" }}>
                <label
                  htmlFor="auth-role"
                  style={{ display: "block", fontSize: "12px", fontWeight: 600, color: "#334155", marginBottom: "5px" }}
                >
                  Workstation Role
                </label>
                <select
                  id="auth-role"
                  value={role}
                  onChange={(e) => setRole(e.target.value as "USER" | "ADMIN")}
                  style={{
                    width: "100%",
                    padding: "9px 12px",
                    fontSize: "13px",
                    borderRadius: "6px",
                    border: "1px solid #cbd5e1",
                    background: "#ffffff",
                    outline: "none",
                    boxSizing: "border-box",
                  }}
                >
                  <option value="USER">USER (Run analysis, manage own jobs & results)</option>
                  <option value="ADMIN">ADMIN (System monitoring, cross-job recovery)</option>
                </select>
              </div>
            </>
          )}

          <button
            type="submit"
            id="btn-auth-submit"
            disabled={loading}
            style={{
              width: "100%",
              padding: "11px",
              backgroundColor: loading ? "#94a3b8" : "#2563eb",
              color: "#ffffff",
              border: "none",
              borderRadius: "6px",
              fontSize: "14px",
              fontWeight: 700,
              cursor: loading ? "not-allowed" : "pointer",
              transition: "background 0.15s ease",
            }}
          >
            {loading ? "Authenticating..." : mode === "login" ? "Sign In" : "Register Account"}
          </button>

          {/* Quick Demo Credentials Helper */}
          <div
            style={{
              marginTop: "16px",
              paddingTop: "14px",
              borderTop: "1px solid #f1f5f9",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
            }}
          >
            <span style={{ fontSize: "11px", color: "#64748b" }}>Quick Autofill:</span>
            <div style={{ display: "flex", gap: "6px" }}>
              <button
                type="button"
                id="btn-demo-user"
                onClick={() => handleDemoFill("USER")}
                style={{
                  fontSize: "11px",
                  padding: "4px 8px",
                  borderRadius: "4px",
                  border: "1px solid #cbd5e1",
                  background: "#f8fafc",
                  color: "#334155",
                  cursor: "pointer",
                }}
              >
                Demo Researcher
              </button>
              <button
                type="button"
                id="btn-demo-admin"
                onClick={() => handleDemoFill("ADMIN")}
                style={{
                  fontSize: "11px",
                  padding: "4px 8px",
                  borderRadius: "4px",
                  border: "1px solid #cbd5e1",
                  background: "#f8fafc",
                  color: "#334155",
                  cursor: "pointer",
                }}
              >
                Demo Admin
              </button>
            </div>
          </div>

          <div
            style={{
              marginTop: "14px",
              fontSize: "10.5px",
              color: "#94a3b8",
              textAlign: "center",
              lineHeight: "1.4",
            }}
          >
            Research Use Only • Application Access Control Layer
          </div>
        </form>
      </div>
    </div>
  );
}
