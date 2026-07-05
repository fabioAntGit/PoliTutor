import { api } from "@/api/client";
import type { UserMemoryListRead } from "@/types/memory";

export async function listMemories(courseId: string): Promise<UserMemoryListRead> {
  const { data } = await api.get<UserMemoryListRead>("/memory", {
    params: { course_id: courseId },
  });
  return data;
}

export async function deleteMemory(memId: string): Promise<void> {
  await api.delete(`/memory/${memId}`);
}
