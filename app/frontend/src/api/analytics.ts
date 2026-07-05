import { api } from "@/api/client";
import type {
  OverviewRead,
  ActivityRead,
  CourseOverviewRead,
  CourseTopicsRead,
  CourseSourcesRead,
} from "@/types/analytics";

export async function getOverview(): Promise<OverviewRead> {
  const { data } = await api.get<OverviewRead>("/analytics/overview");
  return data;
}

export async function getActivity(range: "7d" | "30d" | "90d"): Promise<ActivityRead> {
  const { data } = await api.get<ActivityRead>("/analytics/activity", { params: { range } });
  return data;
}

export async function getCourseOverview(courseId: string): Promise<CourseOverviewRead> {
  const { data } = await api.get<CourseOverviewRead>(`/analytics/courses/${encodeURIComponent(courseId)}/overview`);
  return data;
}

export async function getCourseActivity(courseId: string, range: "7d" | "30d" | "90d"): Promise<ActivityRead> {
  const { data } = await api.get<ActivityRead>(`/analytics/courses/${encodeURIComponent(courseId)}/activity`, { params: { range } });
  return data;
}

export async function getCourseTopics(courseId: string): Promise<CourseTopicsRead> {
  const { data } = await api.get<CourseTopicsRead>(`/analytics/courses/${encodeURIComponent(courseId)}/topics`);
  return data;
}

export async function getCourseSources(courseId: string): Promise<CourseSourcesRead> {
  const { data } = await api.get<CourseSourcesRead>(`/analytics/courses/${encodeURIComponent(courseId)}/sources`);
  return data;
}
