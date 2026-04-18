import * as messagesApi from "@/api/messages";
import type { MessageResponse, MessageSend } from "@/types/message";

export const MessageService = {
  /**
   * Sends a message to the IAEdu agent and processes the API response.
   */
  async sendMessage(
    conversationId: string,
    params: MessageSend,
    config: messagesApi.MessageConfig,
    signal?: AbortSignal
  ): Promise<MessageResponse> {
    return await messagesApi.sendMessage(conversationId, params, config, signal);
  },
};
