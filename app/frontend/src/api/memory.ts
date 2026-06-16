import { api } from "@/api/client";
import type { UserMemoryListRead } from "@/types/memory";

export async function listMemories(course: string): Promise<UserMemoryListRead> {
  const { data } = await api.get<UserMemoryListRead>("/memory", {
    params: { course },
  });
  return data;
}

export async function deleteMemory(memId: string): Promise<void> {
  await api.delete(`/memory/${memId}`);
}
