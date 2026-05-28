export interface CourseCreateRequest {
  code: string;
  name: string;
  description: string;
}

export interface CourseUpdateRequest {
  name?: string;
  description?: string;
  is_active?: boolean;
}
