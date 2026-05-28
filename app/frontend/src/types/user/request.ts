import type { UserRole } from "./enums";

export interface UserCreateRequest {
  email: string;
  password: string;
  full_name: string;
  role: UserRole;
  courses: string[];
}

export interface UserUpdateRequest {
  email?: string;
  full_name?: string;
  role?: UserRole;
  courses?: string[];
}
