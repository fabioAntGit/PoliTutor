import { useNavigate } from "react-router";
import { LogOut, Loader2, Shield } from "lucide-react";

import { ProjectCard } from "@/components/project-card";
import { useHome } from "@/hooks/home/useHome";
import { PageState } from "@/components/ui/page-state";
import { Button } from "@/components/ui/button";
import { authService } from "@/services/auth.service";
import { logout } from "@/api/auth";


export default function HomePage() {
  const navigate = useNavigate();
  const { projects, loading, error, enteringId, enterProject } = useHome();
  const isAdmin = authService.getRole() === "admin";

  const handleLogout = async () => {
    const accessToken = authService.getAccessToken();
    if (accessToken) {
      await logout(accessToken).catch(() => {});
    }
    authService.clearTokens();
    navigate("/login", { replace: true });
  };

  return (
    <PageState
      loading={loading}
      error={error}
      onRetry={() => window.location.reload()}
    >
      <main className="min-h-screen flex items-center justify-center p-6 relative">
        <div className="absolute top-6 right-6 flex items-center gap-1">
          {isAdmin && (
            <Button
              variant="ghost"
              size="icon"
              title="Dashboard admin"
              onClick={() => navigate("/admin")}
            >
              <Shield className="h-5 w-5 text-muted-foreground hover:text-primary transition-colors" />
            </Button>
          )}
          <Button variant="ghost" size="icon" title="Terminar sessão" onClick={handleLogout}>
            <LogOut className="h-5 w-5 text-muted-foreground hover:text-primary transition-colors" />
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
            {projects.length === 0 && (
              <p className="text-muted-foreground text-sm">Nenhum projeto encontrado.</p>
            )}
          </div>
        </div>
      </main>
    </PageState>
  );
}
