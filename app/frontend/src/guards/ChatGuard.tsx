import { Navigate, Outlet, useParams } from "react-router";
import { loadConfig } from "@/services/session.service";

export default function ChatGuard() {
  const { projectId } = useParams();
  const config = loadConfig();

  if (!config) {
    return <Navigate to={`/setup/${projectId}`} replace />;
  }

  return <Outlet />;
}
