export type MemoryType = "difficulty" | "preference" | "goal" | "progress";

export interface UserMemory {
  id: string;
  type: MemoryType;
  content: string;
  last_seen_at: string;
}

export interface UserMemoryListRead {
  memories: UserMemory[];
}
