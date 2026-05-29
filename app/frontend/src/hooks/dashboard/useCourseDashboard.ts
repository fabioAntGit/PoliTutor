import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router";
import { AnalyticsService } from "@/services/analytics.service";
import type { CourseOverview, TopicPoint, SourcePoint } from "@/api/analytics";
import type { RankedListItem } from "@/components/dashboard/ranked-list-card";

type Status = "loading" | "valid" | "not_found";

export function useCourseDashboard() {
  const { courseId } = useParams<{ courseId: string }>();
  const navigate = useNavigate();

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

  const topicItems = useMemo<RankedListItem[] | null>(
    () =>
      topics
        ? topics.map(({ topic, count }) => ({
            key: topic,
            label: topic,
            value: count,
            valueLabel: `${count}×`,
          }))
        : null,
    [topics],
  );

  const sourceItems = useMemo<RankedListItem[] | null>(
    () =>
      sources
        ? sources.map(({ filename, references }) => ({
            key: filename,
            label: filename,
            rawLabel: filename,
            value: references,
            valueLabel: `${references} ref.`,
          }))
        : null,
    [sources],
  );

  return {
    courseId,
    status,
    isLoading: status === "loading",
    overview,
    topicItems,
    sourceItems,
    goToOverview: () => navigate("/dashboard"),
  };
}
