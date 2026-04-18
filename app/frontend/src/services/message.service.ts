import * as messagesApi from "@/api/messages";
import type { AskRequest, AskResponse } from "@/types/ask";

export const MessageService = {
  /**
   * Sends a message to the IAEdu agent and processes the API response.
   */
  async sendMessage(params: AskRequest, signal?: AbortSignal): Promise<AskResponse> {
    return await messagesApi.sendMessage(params, signal);
  },

  /**
   * Retrieves the message history of a conversation session by its ID.
   */
  async getMessages(conversationId: string) {
    return await messagesApi.getMessages({ conversation_id: conversationId });
  }
};
