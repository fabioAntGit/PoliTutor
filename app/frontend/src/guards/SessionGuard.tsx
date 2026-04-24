import { Navigate, Outlet } from "react-router";
import { sessionService } from "@/services/session.service";

export default function SessionGuard() {
  const config = sessionService.loadConfig();

  if (!config) {
    return <Navigate to="/setup" replace />;
  }

  return <Outlet />;
}
