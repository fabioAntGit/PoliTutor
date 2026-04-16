"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { loadConfig } from "@/lib/session-config";
import type { Project } from "@/types/project";
import { ChatUser } from "./chat-user";

interface ChatGuardProps {
  project: Project;
}

export function ChatGuard({ project }: ChatGuardProps) {
  const router = useRouter();

  //useEffect(() => {
    //if (project.configType === "iaedu" && !loadConfig()) {
      //router.replace(`/setup/${project.id}`);
    //}
  //}, [router, project]);

  return <ChatUser project={project} />;
}
