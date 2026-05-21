import * as messagesApi from "@/api/messages";
import type { MessageResponse, MessageSend } from "@/types/message";

export const MessageService = {
  async sendMessage(
    conversationId: string,
    params: MessageSend,
    signal?: AbortSignal
  ): Promise<MessageResponse> {
    return await messagesApi.sendMessage(conversationId, params, signal);
  },
};
