import * as messagesApi from "@/api/messages";
import { sessionService } from "@/services/session.service";
import type { MessageResponse, MessageSend } from "@/types/message";

export const MessageService = {
  /**
   * Orchestrates the message sending logic, gathering the IAEdu config internally.
   */
  async sendMessage(
    conversationId: string,
    params: MessageSend,
    signal?: AbortSignal
  ): Promise<MessageResponse> {
    const config = sessionService.loadConfig();

    if (!config) {
      throw new Error("Configuracao nao encontrada. Por favor, realiza o setup.");
    }

    return await messagesApi.sendMessage(conversationId, params, config, signal);
  },
};
