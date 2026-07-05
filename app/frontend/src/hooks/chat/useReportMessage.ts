import { useState } from "react";
import { toast } from "sonner";
import { ReportService } from "@/services/report.service";

export function useReportMessage(messageId: string, initialReported: boolean) {
  const [reported, setReported] = useState(initialReported);
  const [isReporting, setIsReporting] = useState(false);

  const toggleReport = async () => {
    if (isReporting) return;

    setIsReporting(true);
    try {
      if (reported) {
        const success = await ReportService.unreportMessage(messageId);
        if (success) {
          setReported(false);
        }
      } else {
        const success = await ReportService.reportMessage(messageId);
        if (success) {
          setReported(true);
        } else {
          toast.error("Erro ao enviar o report. Certifica-te que a mensagem já tem uma resposta.");
        }
      }
    } catch (error: unknown) {
      console.error("Erro ao processar report:", error);
      const msg = error instanceof Error ? error.message : "Erro ao processar o pedido. Tenta novamente mais tarde.";
      toast.error(msg);
    } finally {
      setIsReporting(false);
    }
  };

  return { reported, isReporting, toggleReport };
}
