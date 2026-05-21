import { Navigate, Outlet } from "react-router";
import { authService } from "@/services/auth.service";

interface RoleGuardProps {
  roles: string[];
}

export default function RoleGuard({ roles }: RoleGuardProps) {
  const role = authService.getRole();
  if (!role || !roles.includes(role)) {
    return <Navigate to="/" replace />;
  }
  return <Outlet />;
}
