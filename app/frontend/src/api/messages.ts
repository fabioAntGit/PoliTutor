import { api } from "@/api/client";
import type { MessageResponse, MessageSend } from "@/types/message";

export async function sendMessage(
  conversationId: string,
  body: MessageSend,
  signal?: AbortSignal
): Promise<MessageResponse> {
  const response = await api.post<MessageResponse>(`/chat/${conversationId}/messages`, body, {
    signal,
  });
  return response.data;
}
