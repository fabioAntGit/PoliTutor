import { useEffect, useState } from "react";
import { useNavigate } from "react-router";
import { ProjectService } from "@/services/project.service";
import { ChatService } from "@/services/chat.service";
import type { ProjectRead } from "@/types/project";

export function useHome() {
  const navigate = useNavigate();
  const [projects, setProjects] = useState<ProjectRead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Track which project is being initialized (showing a spinner on the card)
  const [enteringId, setEnteringId] = useState<string | null>(null);

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

  const enterProject = async (projectId: string) => {
    if (enteringId) return;

    setEnteringId(projectId);
    try {
      const chat = await ChatService.createChat({ project_id: projectId });
      
      navigate(`/chat/${chat.conversation_id}`);
    } catch (err: any) {
      console.error("Erro ao entrar no projecto:", err);
      alert(err.message || "Erro ao iniciar o chat. Verifica as tuas configurações.");
    } finally {
      setEnteringId(null);
    }
  };

  return {
    projects,
    loading,
    error,
    enteringId,
    enterProject,
  };
}
