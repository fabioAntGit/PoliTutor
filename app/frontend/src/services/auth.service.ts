const ACCESS_TOKEN_KEY = "poli-tutor-access";

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
  getAccessToken(): string | null {
    return localStorage.getItem(ACCESS_TOKEN_KEY);
  },

  setTokens(accessToken: string): void {
    localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
  },

  clearTokens(): void {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
  },

  isAuthenticated(): boolean {
    const token = localStorage.getItem(ACCESS_TOKEN_KEY);
    if (!token) return false;
    if (isExpired(decodePayload(token))) {
      localStorage.removeItem(ACCESS_TOKEN_KEY);
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
