import { useState, useEffect } from "react";
import { AnalyticsService } from "@/services/analytics.service";

export function useSidebarCourses() {
  const [courses, setCourses] = useState<string[] | null>(null);

  useEffect(() => {
    AnalyticsService.getCourses()
      .then((data) => setCourses(data.data))
      .catch(() => setCourses([]));
  }, []);

  return { courses };
}
