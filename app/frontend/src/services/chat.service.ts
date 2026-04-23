import * as chatsApi from "@/api/chats";
import type { ChatCreate, ChatCreated, ChatRead } from "@/types/chat";
import { sessionService } from "./session.service";

export const ChatService = {
  async createChat(params: ChatCreate): Promise<ChatCreated> {
    const config = sessionService.loadConfig();
    if (!config) throw new Error("Configuração não encontrada. Por favor, realiza o setup.");
    
    return await chatsApi.createChat(params, config.channelId);
  },

  async getChat(conversationId: string): Promise<ChatRead> {
    const config = sessionService.loadConfig();
   
    if (!config) throw new Error("Configuração não encontrada.");

    return await chatsApi.getChat(conversationId, config.channelId);
  },
};
