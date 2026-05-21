import { Navigate, Outlet } from "react-router";
import { authService } from "@/services/auth.service";

export default function AuthGuard() {
  if (!authService.isAuthenticated()) {
    return <Navigate to="/login" replace />;
  }
  return <Outlet />;
}
