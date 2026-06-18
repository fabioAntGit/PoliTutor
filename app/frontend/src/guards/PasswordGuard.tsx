import { Navigate, Outlet } from "react-router";
import { authService } from "@/services/auth.service";

export default function PasswordGuard() {
  if (authService.mustChangePassword()) {
    return <Navigate to="/change-password" replace />;
  }
  
  return <Outlet />;
}
