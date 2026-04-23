import { ApiError } from "@/lib/errors";
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
        setProject(res);
      })
      .catch((error) => {
        if (error instanceof ApiError && error.isNotFound) {
          setError("Projeto nao encontrado.");
          return;
        }

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
