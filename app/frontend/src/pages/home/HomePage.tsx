import { Link } from "react-router";
import { Settings, Loader2 } from "lucide-react";

import { ProjectCard } from "@/components/project-card";
import { useHome } from "@/hooks/home/useHome";
import { PageState } from "@/components/ui/page-state";
import { Button } from "@/components/ui/button";

export default function HomePage() {
  const { projects, loading, error, enteringId, enterProject } = useHome();

  return (
    <PageState 
      loading={loading} 
      error={error} 
      onRetry={() => window.location.reload()}
    >
      <main className="min-h-screen flex items-center justify-center p-6 relative">
        {/* Settings Button in Top Right */}
        <div className="absolute top-6 right-6">
          <Button variant="ghost" size="icon" asChild title="Definições de Acesso">
            <Link to="/setup">
              <Settings className="h-5 w-5 text-muted-foreground hover:text-primary transition-colors" />
            </Link>
          </Button>
        </div>

        <div className="w-full max-w-xl space-y-8">
          <div className="space-y-1">
            <h1 className="text-2xl font-semibold tracking-tight">Selecione um projeto para começar.</h1>
          </div>

          <div className="grid gap-3">
            {projects.map((project) => {
              const isEntering = enteringId === project.id;
              
              return (
                <div key={project.id} className="relative group">
                  <ProjectCard 
                    project={project} 
                    selected={isEntering} 
                    onSelect={() => enterProject(project.id)}
                  />
                  {isEntering && (
                    <div className="absolute inset-0 flex items-center justify-center bg-background/50 rounded-lg backdrop-blur-[1px]">
                      <div className="flex items-center gap-2 px-4 py-2 bg-background border rounded-full shadow-lg">
                        <Loader2 className="h-4 w-4 animate-spin text-primary" />
                        <span className="text-xs font-medium">A entrar...</span>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
            {projects.length === 0 && <p className="text-muted-foreground text-sm">Nenhum projeto encontrado.</p>}
          </div>
        </div>
      </main>
    </PageState>
  );
}
