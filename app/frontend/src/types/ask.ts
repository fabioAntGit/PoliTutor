import type { Source } from "./source";

export interface AskRequest {
  conversation_id: string;
  question: string;
  iaedu_endpoint: string;
  iaedu_api_key: string;
  iaedu_channel_id: string;
}

export interface AskResponse {
  answer: string;
  sources: Source[];
  is_fallback: boolean;
  guardrail_triggered: boolean;
}
