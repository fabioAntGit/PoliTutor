import { useState, useEffect } from "react";
import { useIsMobile } from "@/hooks/common/useMobile";
import { AnalyticsService } from "@/services/analytics.service";
import type { ActivityPoint, Range } from "@/types/analytics";

export function useActivityChart(course?: string) {
  const isMobile = useIsMobile();
  const [timeRange, setTimeRange] = useState<Range>("30d");
  const [chartData, setChartData] = useState<ActivityPoint[] | null>(null);

  useEffect(() => {
    if (isMobile) setTimeRange("7d");
  }, [isMobile]);

  useEffect(() => {
    setChartData(null);
    const request = course
      ? AnalyticsService.getCourseActivity(course, timeRange)
      : AnalyticsService.getActivity(timeRange);
    request
      .then((json) => setChartData(json.data))
      .catch(() => setChartData([]));
  }, [timeRange, course]);

  return { timeRange, setTimeRange, chartData };
}
