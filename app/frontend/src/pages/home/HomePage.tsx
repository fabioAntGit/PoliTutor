import { Link } from "react-router";

import { ProjectCard } from "@/components/project-card";
import { useHome } from "@/hooks/home/useHome";
import { PageState } from "@/components/ui/page-state";

export default function HomePage() {
  const { projects, loading, error } = useHome();

  return (
    <PageState 
      loading={loading} 
      error={error} 
      onRetry={() => window.location.reload()}
    >
      <main className="min-h-screen flex items-center justify-center p-6">
        <div className="w-full max-w-xl space-y-8">
          <div className="space-y-1">
            <h1 className="text-2xl font-semibold tracking-tight">Selecione um projeto para começar.</h1>
          </div>

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
        </div>
      </main>
    </PageState>
  );
}
