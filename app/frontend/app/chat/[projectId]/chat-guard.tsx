"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { loadConfig } from "@/lib/session-config";
import type { Project } from "@/types/project";

interface ChatGuardProps {
  project: Project;
}

export function ChatGuard({ project }: ChatGuardProps) {
  const router = useRouter();

  useEffect(() => {
    if (project.configType === "iaedu" && !loadConfig()) {
      router.replace(`/setup/${project.id}`);
    }
  }, [router, project]);

  return (
    <main className="min-h-screen flex items-center justify-center p-6">
      <div className="text-center space-y-2">
        <h1 className="text-2xl font-semibold tracking-tight">{project.name}</h1>
        <p className="text-sm text-muted-foreground">
          Página de chat — em desenvolvimento.
        </p>
      </div>
    </main>
  );
}
