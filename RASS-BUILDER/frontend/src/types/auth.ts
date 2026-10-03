/**
 * RASS-BUILDER: Stage 9 Authentication & Access Control Types
 * Defines user identities, authentication tokens, session states, and role constants.
 */

export type UserRole = "USER" | "ADMIN";

export type AccountStatus = "ACTIVE" | "SUSPENDED";

export interface User {
  user_id: string;
  name: string;
  email: string;
  role: UserRole;
  account_status: AccountStatus;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}
