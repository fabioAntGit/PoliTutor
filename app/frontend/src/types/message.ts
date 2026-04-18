import type { Source } from "./source";

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  createdAt: string;
  sources?: Source[];
  isFallback?: boolean;
}