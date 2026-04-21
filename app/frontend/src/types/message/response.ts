import type { Source } from "./models";

export interface MessageResponse {
  answer: string;
  sources: Source[];
  is_fallback: boolean;
  guardrail_triggered: boolean;
}
