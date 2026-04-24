import * as reportsApi from "@/api/reports";
import { sessionService } from "./session.service";

export const ReportService = {
  async reportMessage(
    messageId: string
  ): Promise<boolean> {
    const config = sessionService.loadConfig();
    if (!config) throw new Error("Configuração não encontrada.");

    const response = await reportsApi.sendReport(messageId, config.channelId);
    return response.success;
  },

  async unreportMessage(
    messageId: string
  ): Promise<boolean> {
    const config = sessionService.loadConfig();
    if (!config) throw new Error("Configuração não encontrada.");

    const response = await reportsApi.deleteReport(messageId, config.channelId);
    return response.success;
  },
};
