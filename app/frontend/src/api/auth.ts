import { api } from "@/api/client";
import type { LoginResponse } from "@/types/auth";

export async function login(username: string, password: string): Promise<LoginResponse> {
  const form = new URLSearchParams({ username, password });
  const res = await api.post<LoginResponse>("/auth/login", form, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
  return res.data;
}

export async function logout(accessToken: string): Promise<void> {
  await api.post("/auth/logout", { access_token: accessToken });
}

export async function changePassword(
  currentPassword: string,
  newPassword: string,
): Promise<LoginResponse> {
  const res = await api.post<LoginResponse>("/auth/change-password", {
    current_password: currentPassword,
    new_password: newPassword,
  });
  return res.data;
}
