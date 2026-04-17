import * as messagesApi from "@/api/messages";
// import type { Message } from "@/types/message";

export const MessageService = {
  /**
   * Sends a message to the IAEdu agent and processes the API response.
   */
  async sendMessage(params: {
    conversation_id: string;
    question: string;
    iaedu_endpoint: string;
    iaedu_api_key: string;
    iaedu_channel_id: string;
  }) {
    return await messagesApi.sendMessage(params);
  },

  /**
   * Retrieves the message history of a conversation session by its ID.
   */
  async getMessages(conversationId: string) {
    return await messagesApi.getMessages({ conversation_id: conversationId });
  }
};
