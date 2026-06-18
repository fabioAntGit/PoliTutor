import { Navigate, Outlet } from "react-router";
import { authService } from "@/services/auth.service";
import { landingForRole } from "@/lib/landing";

interface RoleGuardProps {
  roles: string[];
  fallback?: string;
}

export default function RoleGuard({ roles, fallback }: RoleGuardProps) {
  const role = authService.getRole();

  if (!role || !roles.includes(role)) {
    return <Navigate to={fallback ?? landingForRole(role)} replace />;
  }
  
  return <Outlet />;
}
