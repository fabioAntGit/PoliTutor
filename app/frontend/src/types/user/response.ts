import type { UserRole } from "./enums";

export interface UserResponse {
  username: string;
  email: string;
  full_name: string;
  role: UserRole;
  courses: string[];
  is_active: boolean;
  must_change_password: boolean;
}
