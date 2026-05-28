import { useEffect, useState } from "react";
import { AnalyticsService } from "@/services/analytics.service";
import type { OverviewData } from "@/api/analytics";

export function useDashboard() {
  const [overview, setOverview] = useState<OverviewData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    AnalyticsService.getOverview()
      .then(setOverview)
      .catch(() => setError("Não foi possível carregar os dados gerais."))
      .finally(() => setLoading(false));
  }, []);

  return { overview, loading, error };
}
