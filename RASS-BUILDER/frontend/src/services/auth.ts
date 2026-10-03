/**
 * RASS-BUILDER: Stage 9 Authentication Service
 * Manages user registration, login, logout, token persistence, and session verification.
 */

import type { User, TokenResponse } from "../types/auth";

const API_BASE_URL =
  (import.meta.env?.VITE_API_BASE_URL as string) ||
  (typeof window !== "undefined" && window.location.hostname !== "localhost" && window.location.hostname !== "127.0.0.1"
    ? window.location.origin
    : "http://localhost:8000");
const TOKEN_STORAGE_KEY = "rass_builder_auth_token";

export function getStoredToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_STORAGE_KEY);
  } catch {
    return null;
  }
}

export function setStoredToken(token: string): void {
  try {
    localStorage.setItem(TOKEN_STORAGE_KEY, token);
  } catch {
    // Ignore storage errors in restricted contexts
  }
}

export function removeStoredToken(): void {
  try {
    localStorage.removeItem(TOKEN_STORAGE_KEY);
  } catch {
    // Ignore storage errors
  }
}

export function getAuthHeaders(): HeadersInit {
  const token = getStoredToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  return headers;
}

export async function register(
  name: string,
  email: string,
  password: string,
  confirmPassword: string,
  role: "USER" | "ADMIN" = "USER"
): Promise<TokenResponse> {
  const response = await fetch(`${API_BASE_URL}/api/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      name,
      email,
      password,
      confirm_password: confirmPassword,
      role,
    }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Registration failed." }));
    throw new Error(error.detail || "Registration failed.");
  }

  const data: TokenResponse = await response.json();
  setStoredToken(data.access_token);
  return data;
}

export async function login(email: string, password: string): Promise<TokenResponse> {
  const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Login failed." }));
    throw new Error(error.detail || "Invalid email or password.");
  }

  const data: TokenResponse = await response.json();
  setStoredToken(data.access_token);
  return data;
}

export async function logout(): Promise<void> {
  const token = getStoredToken();
  if (token) {
    try {
      await fetch(`${API_BASE_URL}/api/auth/logout`, {
        method: "POST",
        headers: getAuthHeaders(),
      });
    } catch {
      // Ignore network errors on logout
    }
  }
  removeStoredToken();
}

export async function getMe(): Promise<User> {
  const token = getStoredToken();
  if (!token) {
    throw new Error("No active session token.");
  }

  const response = await fetch(`${API_BASE_URL}/api/auth/me`, {
    method: "GET",
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    removeStoredToken();
    const error = await response.json().catch(() => ({ detail: "Session expired." }));
    throw new Error(error.detail || "Session expired.");
  }

  return response.json();
}
