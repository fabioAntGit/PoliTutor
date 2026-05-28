import { api } from "@/api/client";
import type { ChatCreate, ChatCreated, ChatListItem, ChatRead } from "@/types/chat";

export async function createChat(body: ChatCreate): Promise<ChatCreated> {
  const response = await api.post<ChatCreated>("/chat", body);
  return response.data;
}

export async function getChat(conversationId: string): Promise<ChatRead> {
  const response = await api.get<ChatRead>(`/chat/${encodeURIComponent(conversationId)}`);
  return response.data;
}

export async function listChats(): Promise<ChatListItem[]> {
  const response = await api.get<ChatListItem[]>("/chats");
  return response.data;
}
