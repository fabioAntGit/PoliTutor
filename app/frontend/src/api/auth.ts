import axios from "axios";
import { api } from "@/api/client";
import type { AuthTokens } from "@/types/auth";

const baseURL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";

export async function login(username: string, password: string): Promise<AuthTokens> {
  const form = new URLSearchParams({ username, password });
  const res = await axios.post<AuthTokens>(`${baseURL}/auth/login`, form, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
  return res.data;
}

export async function logout(accessToken: string): Promise<void> {
  await axios.post(`${baseURL}/auth/logout`, { access_token: accessToken });
}

export async function changePassword(
  currentPassword: string,
  newPassword: string,
): Promise<AuthTokens> {
  const res = await api.post<AuthTokens>("/auth/change-password", {
    current_password: currentPassword,
    new_password: newPassword,
  });
  return res.data;
}
