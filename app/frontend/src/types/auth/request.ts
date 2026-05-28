export interface LoginRequest {
  username: string;
  password: string;
}

export interface LogoutRequest {
  access_token: string;
}
