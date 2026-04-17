import type { SetupFormValues } from "@/schemas/setup";

const STORAGE_KEY = "poli-tutor-config";

export function saveConfig(data: SetupFormValues): void {
  sessionStorage.setItem(STORAGE_KEY, JSON.stringify(data));
}

export function loadConfig(): SetupFormValues | null {
  if (typeof window === "undefined") return null;

  const raw = sessionStorage.getItem(STORAGE_KEY);
  console.log(raw);

  if (!raw) return null;
  try {
    return JSON.parse(raw) as SetupFormValues;
  } catch {
    return null;
  }
}

export function clearConfig(): void {
  sessionStorage.removeItem(STORAGE_KEY);
}