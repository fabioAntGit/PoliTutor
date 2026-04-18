import { Navigate, Outlet, useParams } from "react-router";
import { sessionService } from "@/services/session.service";

export default function ChatGuard() {
  const { projectId } = useParams();
  const config = sessionService.loadConfig();

  if (!config) {
    return <Navigate to={`/setup/${projectId}`} replace />;
  }

  return <Outlet />;
}
