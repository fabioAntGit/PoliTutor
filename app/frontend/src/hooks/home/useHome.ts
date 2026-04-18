import { useEffect, useState } from "react";
import { ProjectService } from "@/services/project.service";
import type { Project } from "@/types/project";

export function useHome() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    ProjectService.getAllProjects()
      .then((data) => {
        setProjects(data);
      })
      .catch(() => {
        setError("Não foi possível carregar os projetos. Tenta novamente mais tarde.");
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  return {
    projects,
    loading,
    error,
  };
}
