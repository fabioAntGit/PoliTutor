import type { Message } from "@/types/message";

export interface ChatCreated {
  conversation_id: string;
}

export interface ChatRead {
  conversation_id: string;
  project_id: string;
  project_name: string;
  user_id: string;
  summary?: string | null;
  messages: Message[];
}
