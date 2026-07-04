import type { Message } from "@/types/message";

export interface ChatCreated {
  conversation_id: string;
}

export interface ChatRead {
  course_name: string;
  messages: Message[];
}

export interface ChatListItem {
  conversation_id: string;
  course_name: string;
  updated_at: string;
}
