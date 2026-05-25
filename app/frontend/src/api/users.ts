import { api } from "@/api/client";
import type { UserResponse, UserCreateRequest, UserUpdateRequest } from "@/types/user";

export async function listUsers(): Promise<UserResponse[]> {
  const res = await api.get<UserResponse[]>("/users");
  return res.data;
}

export async function getUser(username: string): Promise<UserResponse> {
  const res = await api.get<UserResponse>(`/users/${username}`);
  return res.data;
}

export async function createUser(body: UserCreateRequest): Promise<UserResponse> {
  const res = await api.post<UserResponse>("/users", body);
  return res.data;
}

export async function updateUser(username: string, body: UserUpdateRequest): Promise<UserResponse> {
  const res = await api.put<UserResponse>(`/users/${username}`, body);
  return res.data;
}

export async function deleteUser(username: string): Promise<void> {
  await api.delete(`/users/${username}`);
}

export async function deleteMyAccount(): Promise<void> {
  await api.delete("/users/me");
}

