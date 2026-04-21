import { useEffect, useState } from "react";
import { useParams } from "react-router";
import { ProjectService } from "@/services/project.service";
import type { ProjectRead } from "@/types/project";

export function useProject() {
  const { projectId } = useParams();
  const [project, setProject] = useState<ProjectRead | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!projectId) {
      setLoading(false);
      return;
    }

    ProjectService.getProjectById(projectId)
      .then((res) => {
        if (res) {
          setProject(res);
        } else {
          setError("Projeto não encontrado.");
        }
      })
      .catch(() => {
        setError("Erro ao carregar os dados do projeto.");
      })
      .finally(() => {
        setLoading(false);
      });
  }, [projectId]);

  return {
    projectId,
    project,
    loading,
    error,
  };
}
