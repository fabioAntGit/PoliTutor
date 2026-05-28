import * as reportsApi from "@/api/reports";

export const ReportService = {
  async reportMessage(messageId: string): Promise<boolean> {
    const response = await reportsApi.sendReport(messageId);
    return response.success;
  },

  async unreportMessage(messageId: string): Promise<boolean> {
    const response = await reportsApi.deleteReport(messageId);
    return response.success;
  },
};
