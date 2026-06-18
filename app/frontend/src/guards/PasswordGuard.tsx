import { Navigate, Outlet } from "react-router";
import { AuthService } from "@/services/auth.service";

export default function PasswordGuard() {
  if (AuthService.mustChangePassword()) {
    return <Navigate to="/change-password" replace />;
  }
  
  return <Outlet />;
}
