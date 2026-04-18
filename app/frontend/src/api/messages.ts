import { api } from "@/api/client";
import type { AskRequest, AskResponse } from "@/types/ask";
import type { Message } from "@/types/message";

export async function sendMessage(body: AskRequest, signal?: AbortSignal): Promise<AskResponse> {
  try {
    const response = await api.post<AskResponse>("/ask", body, { signal });
    return response.data;
  } catch (error: any) {
    if (error.name === "CanceledError" || error.message === "canceled") {
      throw error;
    }
    throw new Error(error.response?.data?.detail ?? "Erro ao enviar mensagem.");
  }
}

export async function getMessages(params: { conversation_id: string }): Promise<Message[]> {
  try {
    const response = await api.get<Message[]>("/messages", { params });
    return response.data;
  } catch (error: any) {
    throw new Error(error.response?.data?.detail ?? "Erro ao obter mensagens.");
  }
}
