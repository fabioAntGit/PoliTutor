import { Navigate, Outlet } from "react-router";
import { AuthService } from "@/services/auth.service";

export default function AuthGuard() {
  if (!AuthService.isAuthenticated()) {
    return <Navigate to="/login" replace />;
  }
  
  return <Outlet />;
}
