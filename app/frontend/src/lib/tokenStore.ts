const ACCESS_TOKEN_KEY = "poli-tutor-access";

export const tokenStore = {
  get(): string | null {
    return localStorage.getItem(ACCESS_TOKEN_KEY);
  },

  set(accessToken: string): void {
    localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
  },

  clear(): void {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
  },
};
