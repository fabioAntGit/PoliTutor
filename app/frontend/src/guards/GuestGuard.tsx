import { Navigate, Outlet } from "react-router";
import { authService } from "@/services/auth.service";

export default function GuestGuard() {
  if (authService.isAuthenticated()) {
    return <Navigate to="/" replace />;
  }
  return <Outlet />;
}
