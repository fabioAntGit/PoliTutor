import * as chatsApi from "@/api/chats";
import type { ChatCreate, ChatCreated, ChatListItem, ChatRead } from "@/types/chat";

export const ChatService = {
  async createChat(params: ChatCreate): Promise<ChatCreated> {
    return await chatsApi.createChat(params);
  },

  async getChat(conversationId: string): Promise<ChatRead> {
    return await chatsApi.getChat(conversationId);
  },

  async listChats(): Promise<ChatListItem[]> {
    return await chatsApi.listChats();
  },

  async deleteChat(conversationId: string): Promise<void> {
    await chatsApi.deleteChat(conversationId);
  },
};
