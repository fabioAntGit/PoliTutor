import { api } from "@/api/client";

export type MemoryType = "difficulty" | "preference" | "goal" | "progress";

export interface UserMemory {
  id: string;
  course: string;
  type: MemoryType;
  topic: string;
  content: string;
  importance: number;
  last_seen_at: string;
  created_at: string;
}

export interface UserMemoryListResponse {
  memories: UserMemory[];
  total: number;
}

export async function listMemories(course: string): Promise<UserMemoryListResponse> {
  const { data } = await api.get<UserMemoryListResponse>("/memory", {
    params: { course },
  });
  return data;
}

export async function deleteMemory(memId: string): Promise<void> {
  await api.delete(`/memory/${memId}`);
}
