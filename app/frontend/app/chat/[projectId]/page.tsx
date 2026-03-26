import { notFound } from "next/navigation";
import { PROJECTS } from "@/constants/projects";
import { ChatGuard } from "./chat-guard";

interface ChatPageProps {
  params: Promise<{ projectId: string }>;
}

export default async function ChatPage({ params }: ChatPageProps) {
  const { projectId } = await params;
  const project = PROJECTS.find((p) => p.id === projectId);

  if (!project) notFound();

  return <ChatGuard project={project} />;
}