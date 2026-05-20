import { useEffect, useState } from "react";
import { ProjectService } from "@/services/project.service";

interface UseProjectDescriptionResult {
  description: string;
  loading: boolean;
}

export function useProjectDescription(projectId?: string): UseProjectDescriptionResult {
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!projectId) {
      setDescription("");
      setLoading(false);
      return;
    }

    let cancelled = false;
    setLoading(true);

    ProjectService.getProjectDescription(projectId)
      .then((response) => {
        if (!cancelled) {
          setDescription(response.description || "");
        }
      })
      .catch(() => {
        if (!cancelled) {
          setDescription("");
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [projectId]);

  return { description, loading };
}
