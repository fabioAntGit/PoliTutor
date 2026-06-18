import { Navigate, Outlet } from "react-router";
import { AuthService } from "@/services/auth.service";

export default function GuestGuard() {
  if (AuthService.isAuthenticated()) {
    return <Navigate to="/" replace />;
  }
  
  return <Outlet />;
}
