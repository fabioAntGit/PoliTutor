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

export interface UserMemoryListRead {
  memories: UserMemory[];
  total: number;
}
