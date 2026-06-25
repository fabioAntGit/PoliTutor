import type { UserRole } from "./enums";

export interface UserResponse {
  username: string;
  email: string;
  full_name: string;
  role: UserRole;
  courses: string[];
  must_change_password: boolean;
}

export interface CreatedUserCredentials {
  username: string;
  password: string;
}
