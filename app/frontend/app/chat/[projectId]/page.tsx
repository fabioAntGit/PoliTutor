import { notFound } from "next/navigation";
import { getProject } from "@/lib/api-helpers/projects";
import { ChatGuard } from "./chat-guard";

interface ChatPageProps {
  params: Promise<{ projectId: string }>;
}

export default async function ChatPage({ params }: ChatPageProps) {
  const { projectId } = await params;
  const project = await getProject(projectId);

  if (!project) notFound();

  return <ChatGuard project={project} />;
}
