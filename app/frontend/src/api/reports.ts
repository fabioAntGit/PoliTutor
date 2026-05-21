import { api } from "@/api/client";
import type { ReportResponse } from "@/types/report";

export async function sendReport(messageId: string): Promise<ReportResponse> {
  const response = await api.post<ReportResponse>(`/report/${messageId}`);
  return response.data;
}

export async function deleteReport(messageId: string): Promise<ReportResponse> {
  const response = await api.delete<ReportResponse>(`/report/${messageId}`);
  return response.data;
}
