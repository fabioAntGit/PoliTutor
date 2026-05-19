import { api } from "@/api/client";

export interface OverviewData {
  total_conversations: number;
  active_students: number;
  total_messages: number;
  avg_questions_per_conversation: number;
}

export interface ActivityPoint {
  date: string;
  questions: number;
}

export interface ActivityData {
  data: ActivityPoint[];
}

export interface CoursesData {
  data: string[];
}

export interface CourseOverview {
  course: string;
  total_conversations: number;
  active_students: number;
  total_messages: number;
  avg_questions_per_conversation: number;
}

export interface TopicPoint {
  topic: string;
  count: number;
}

export interface CourseTopicsData {
  course: string;
  topics: TopicPoint[];
}

export interface SourcePoint {
  filename: string;
  references: number;
}

export interface CourseSourcesData {
  course: string;
  sources: SourcePoint[];
}

export async function getOverview(): Promise<OverviewData> {
  const { data } = await api.get<OverviewData>("/analytics/overview");
  return data;
}

export async function getActivity(range: "7d" | "30d" | "90d"): Promise<ActivityData> {
  const { data } = await api.get<ActivityData>("/analytics/activity", { params: { range } });
  return data;
}

export async function getCourses(): Promise<CoursesData> {
  const { data } = await api.get<CoursesData>("/analytics/courses");
  return data;
}

export async function getCourseOverview(course: string): Promise<CourseOverview> {
  const { data } = await api.get<CourseOverview>(`/analytics/courses/${encodeURIComponent(course)}/overview`);
  return data;
}

export async function getCourseActivity(course: string, range: "7d" | "30d" | "90d"): Promise<ActivityData> {
  const { data } = await api.get<ActivityData>(`/analytics/courses/${encodeURIComponent(course)}/activity`, { params: { range } });
  return data;
}

export async function getCourseTopics(course: string): Promise<CourseTopicsData> {
  const { data } = await api.get<CourseTopicsData>(`/analytics/courses/${encodeURIComponent(course)}/topics`);
  return data;
}

export async function getCourseSources(course: string): Promise<CourseSourcesData> {
  const { data } = await api.get<CourseSourcesData>(`/analytics/courses/${encodeURIComponent(course)}/sources`);
  return data;
}
