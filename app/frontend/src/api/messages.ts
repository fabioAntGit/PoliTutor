import { api } from "@/api/client";
import type { IAEduConfig } from "@/types/iaedu";
import type { MessageResponse, MessageSend } from "@/types/message";

export async function sendMessage(
  conversationId: string,
  body: MessageSend,
  config: IAEduConfig,
  signal?: AbortSignal
): Promise<MessageResponse> {
  try {
    const response = await api.post<MessageResponse>(`/chat/${conversationId}/messages`, body, {
      headers: {
        "X-IAEdu-API-Key": config.apiKey,
        "X-IAEdu-Endpoint": config.endpoint,
        "X-IAEdu-Channel-ID": config.channelId,
      },
      signal,
    });
    return response.data;
  } catch (error: any) {
    if (error.name === "CanceledError" || error.message === "canceled") {
      throw error;
    }

    if (error.response?.status === 422) {
      throw new Error("Credenciais invalidas. Por favor, verifica o teu Endpoint, API Key e Channel ID nas definicoes.");
    }

    throw new Error(error.response?.data?.message || "Erro ao enviar mensagem.");
  }
}
