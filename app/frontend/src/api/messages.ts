import { api } from "@/api/client";
import type { IAEduConfig } from "@/types/iaedu";
import type { MessageResponse, MessageSend } from "@/types/message";

export async function sendMessage(
  conversationId: string,
  body: MessageSend,
  config: IAEduConfig,
  signal?: AbortSignal
): Promise<MessageResponse> {
  const response = await api.post<MessageResponse>(`/chat/${conversationId}/messages`, body, {
    headers: {
      "X-IAEdu-API-Key": config.apiKey,
      "X-IAEdu-Endpoint": config.endpoint,
      "X-IAEdu-Channel-ID": config.channelId,
    },
    signal,
  });
  return response.data;
}
