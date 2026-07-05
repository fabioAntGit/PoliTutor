import { api } from "@/api/client";
import type {
  CourseResponse,
  CourseCreateRequest,
  CourseUpdateRequest,
} from "@/types/course";

export async function listCourses(): Promise<CourseResponse[]> {
  const res = await api.get<CourseResponse[]>("/courses");
  return res.data;
}

export async function listAllCourses(): Promise<CourseResponse[]> {
  const res = await api.get<CourseResponse[]>("/courses/all");
  return res.data;
}

export async function listActiveCourses(): Promise<CourseResponse[]> {
  const res = await api.get<CourseResponse[]>("/courses/active");
  return res.data;
}

export async function createCourse(body: CourseCreateRequest): Promise<CourseResponse> {
  const res = await api.post<CourseResponse>("/courses", body);
  return res.data;
}

export async function updateCourse(
  courseId: string,
  body: CourseUpdateRequest,
): Promise<CourseResponse> {
  const res = await api.put<CourseResponse>(`/courses/${courseId}`, body);
  return res.data;
}

export async function deleteCourse(courseId: string): Promise<void> {
  await api.delete(`/courses/${courseId}`);
}
