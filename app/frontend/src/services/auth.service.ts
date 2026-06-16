import { tokenStore } from "@/lib/tokenStore";
import {
  login as loginRequest,
  logout as logoutRequest,
  changePassword as changePasswordRequest,
} from "@/api/auth";
import type { LoginResponse } from "@/types/auth";

function decodePayload(token: string): Record<string, unknown> {
  try {
    const base64 = token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/");
    return JSON.parse(atob(base64));
  } catch {
    return {};
  }
}

function isExpired(payload: Record<string, unknown>): boolean {
  const exp = payload.exp;
  if (typeof exp !== "number") return true;
  return exp * 1000 <= Date.now();
}

export const authService = {
  login(username: string, password: string): Promise<LoginResponse> {
    return loginRequest(username, password);
  },

  logout(accessToken: string): Promise<void> {
    return logoutRequest(accessToken);
  },

  changePassword(currentPassword: string, newPassword: string): Promise<LoginResponse> {
    return changePasswordRequest(currentPassword, newPassword);
  },

  getAccessToken(): string | null {
    return tokenStore.get();
  },

  setTokens(accessToken: string): void {
    tokenStore.set(accessToken);
  },

  clearTokens(): void {
    tokenStore.clear();
  },

  isAuthenticated(): boolean {
    const token = tokenStore.get();
    if (!token) return false;
    if (isExpired(decodePayload(token))) {
      tokenStore.clear();
      return false;
    }
    return true;
  },

  getPayload(): Record<string, unknown> | null {
    const token = this.getAccessToken();
    if (!token) return null;
    return decodePayload(token);
  },

  getRole(): string | null {
    return (this.getPayload()?.role as string) ?? null;
  },

  getFullName(): string | null {
    return (this.getPayload()?.full_name as string) ?? null;
  },

  getUsername(): string | null {
    return (this.getPayload()?.username as string) ?? null;
  },

  getCourses(): string[] {
    const raw = this.getPayload()?.courses;
    return Array.isArray(raw) ? (raw as string[]) : [];
  },

  mustChangePassword(): boolean {
    return Boolean(this.getPayload()?.must_change_password);
  },
};
