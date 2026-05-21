import { api } from "@/api/client";
import type { CourseResponse, CourseCreateRequest } from "@/types/course";

export async function listCourses(): Promise<CourseResponse[]> {
  const res = await api.get<CourseResponse[]>("/courses");
  return res.data;
}

export async function createCourse(body: CourseCreateRequest): Promise<CourseResponse> {
  const res = await api.post<CourseResponse>("/courses", body);
  return res.data;
}
