import * as chatsApi from "@/api/chats";
import type { ChatCreate, ChatCreated, ChatRead } from "@/types/chat";

export const ChatService = {
  async createChat(params: ChatCreate): Promise<ChatCreated> {
    return await chatsApi.createChat(params);
  },

  async getChat(conversationId: string): Promise<ChatRead> {
    return await chatsApi.getChat(conversationId);
  },
};
