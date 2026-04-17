import { Link } from "react-router";
import { useEffect, useState } from "react";
import type { Project } from "@/types/project";
import { Loader2 } from "lucide-react";

import { ProjectCard } from "@/components/project-card";
import { ProjectService } from "@/services/project.service";

export default function HomePage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    ProjectService.getAllProjects().then(data => {
      setProjects(data);
      setLoading(false);
    });
  }, []);

  return (
    <main className="min-h-screen flex items-center justify-center p-6">
      <div className="w-full max-w-xl space-y-8">
        <div className="space-y-1">
          <h1 className="text-2xl font-semibold tracking-tight">Selecione um projeto para começar.</h1>
        </div>

        {loading ? (
          <div className="flex justify-center"><Loader2 className="animate-spin" /></div>
        ) : (
          <div className="grid gap-3">
          {projects.map((project) => (
            <Link
              key={project.id}
              to={
                project.configType === "iaedu"
                  ? `/setup/${project.id}`
                  : `/chat/${project.id}`
              }
            >
              <ProjectCard project={project} selected={false} />
            </Link>
          ))}
          {projects.length === 0 && <p className="text-muted-foreground text-sm">Nenhum projeto encontrado.</p>}
        </div>
        )}
      </div>
    </main>
  );
}
