import type { IAEduConfig } from "@/types/iaedu";

const STORAGE_KEY = "poli-tutor-config";

export const sessionService = {
  /**
   * Saves the configuration to sessionStorage.
   */
  saveConfig(data: IAEduConfig): void {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(data));
  },

  /**
   * Loads the configuration from sessionStorage.
   */
  loadConfig(): IAEduConfig | null {
    if (typeof window === "undefined") return null;

    const raw = sessionStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    try {
      return JSON.parse(raw) as IAEduConfig;
    } catch {
      return null;
    }
  },

  /**
   * Clears the configuration from sessionStorage.
   */
  clearConfig(): void {
    sessionStorage.removeItem(STORAGE_KEY);
  }
};
