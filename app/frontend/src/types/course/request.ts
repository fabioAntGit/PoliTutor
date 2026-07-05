export interface CourseCreateRequest {
  code: string;
  name: string;
  scope: string;
}

export interface CourseUpdateRequest {
  name?: string;
  scope?: string;
  is_active?: boolean;
}
