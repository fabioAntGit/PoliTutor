import { useEffect, useState } from "react";
import { useParams } from "react-router";
import { AnalyticsService } from "@/services/analytics.service";
import type { CourseOverview, TopicPoint, SourcePoint } from "@/api/analytics";

type Status = "loading" | "valid" | "not_found";

export function useCourseDashboard() {
  const { courseId } = useParams<{ courseId: string }>();

  const [status, setStatus] = useState<Status>("loading");
  const [overview, setOverview] = useState<CourseOverview | null>(null);
  const [topics, setTopics] = useState<TopicPoint[] | null>(null);
  const [sources, setSources] = useState<SourcePoint[] | null>(null);

  useEffect(() => {
    if (!courseId) return;

    setStatus("loading");
    setOverview(null);
    setTopics(null);
    setSources(null);

    AnalyticsService.getCourses()
      .then(({ data: courses }) => {
        const exists = courses.some((c) => c === courseId);
        if (!exists) {
          setStatus("not_found");
          return;
        }

        return Promise.all([
          AnalyticsService.getCourseOverview(courseId),
          AnalyticsService.getCourseTopics(courseId),
          AnalyticsService.getCourseSources(courseId),
        ]).then(([ov, tp, sr]) => {
          setOverview(ov);
          setTopics(tp.topics);
          setSources(sr.sources);
          setStatus("valid");
        });
      })
      .catch(() => setStatus("not_found"));
  }, [courseId]);

  return { courseId, status, overview, topics, sources };
}
