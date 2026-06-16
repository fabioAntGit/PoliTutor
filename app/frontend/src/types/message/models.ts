export type Role = "user" | "assistant";

export interface Source {
  filename: string;
  pages?: number[];
}

export interface Message {
  id: string;
  role: Role;
  content: string;
  created_at: string;
  sources?: Source[];
  is_fallback?: boolean;
  is_reported?: boolean;
}
