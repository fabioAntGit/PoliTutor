import { api } from "@/api/client";
import type { ChatCreate, ChatCreated, ChatRead } from "@/types/chat";

export async function createChat(body: ChatCreate): Promise<ChatCreated> {
  try {
    const response = await api.post<ChatCreated>("/chat", body);
    return response.data;
  } catch (error: any) {
    throw new Error(error.response?.data?.message ?? "Erro ao criar chat.");
  }
}


export async function getChat(conversationId: string): Promise<ChatRead> {
  try {
    const response = await api.get<ChatRead>(`/chat/${encodeURIComponent(conversationId)}`);
    return response.data;
  } catch (error: any) {
    throw new Error(error.response?.data?.message ?? "Erro ao obter chat.");
  }
}
