import { useNavigate } from "react-router";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { setupSchema, type SetupFormValues } from "@/schemas/setup";
import { sessionService } from "@/services/session.service";
import { useProject } from "@/hooks/shared/useProject";
import { ChatService } from "@/services/chat.service";

export function useSetup() {
  const navigate = useNavigate();
  const { project, loading, error } = useProject();

  const form = useForm<SetupFormValues>({
    resolver: zodResolver(setupSchema),
    mode: "onBlur",
  });

  const onSubmit = async (data: SetupFormValues) => {
    form.clearErrors("root");

    if (!project) return;

    try {
      const chat = await ChatService.createChat({
        project_id: project.id,
        user_id: data.channelId,
      });

      sessionService.saveConfig(data);

      navigate(`/chat/${chat.conversation_id}`);
    } catch (error) {
      form.setError("root", {
        message: error instanceof Error ? error.message : "Erro ao criar chat.",
      });
    }
  };

  return {
    project,
    loading,
    error,
    form,
    onSubmit: form.handleSubmit(onSubmit),
  };
}
