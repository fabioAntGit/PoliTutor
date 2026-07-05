import type { Source } from "./models";

export interface MessageResponse {
  user_message_id: string;
  assistant_message_id: string;
  answer: string;
  sources: Source[];
  is_fallback: boolean;
}
