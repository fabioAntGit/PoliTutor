export type Role = "user" | "assistant";

export interface Source {
  filename: string;
  pages?: number[];
}

export interface Message {
  id: string;
  role: Role;
  content: string;
  createdAt: string;
  sources?: Source[];
  isFallback?: boolean;
  is_reported?: boolean;
}
