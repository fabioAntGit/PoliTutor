import { api } from "@/api/client";
import type {
  OverviewRead,
  ActivityRead,
  CoursesRead,
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

export async function getCourses(): Promise<CoursesRead> {
  const { data } = await api.get<CoursesRead>("/analytics/courses");
  return data;
}

export async function getCourseOverview(course: string): Promise<CourseOverviewRead> {
  const { data } = await api.get<CourseOverviewRead>(`/analytics/courses/${encodeURIComponent(course)}/overview`);
  return data;
}

export async function getCourseActivity(course: string, range: "7d" | "30d" | "90d"): Promise<ActivityRead> {
  const { data } = await api.get<ActivityRead>(`/analytics/courses/${encodeURIComponent(course)}/activity`, { params: { range } });
  return data;
}

export async function getCourseTopics(course: string): Promise<CourseTopicsRead> {
  const { data } = await api.get<CourseTopicsRead>(`/analytics/courses/${encodeURIComponent(course)}/topics`);
  return data;
}

export async function getCourseSources(course: string): Promise<CourseSourcesRead> {
  const { data } = await api.get<CourseSourcesRead>(`/analytics/courses/${encodeURIComponent(course)}/sources`);
  return data;
}
