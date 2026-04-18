import { useNavigate } from "react-router";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { setupSchema, type SetupFormValues } from "@/schemas/setup";
import { sessionService } from "@/services/session.service";
import { useProject } from "@/hooks/shared/useProject";

export function useSetup() {
  const navigate = useNavigate();
  const { project, loading, error } = useProject();

  const form = useForm<SetupFormValues>({
    resolver: zodResolver(setupSchema),
    mode: "onBlur",
  });

  const onSubmit = (data: SetupFormValues) => {
    sessionService.saveConfig(data);
    if (project) {
      navigate(`/chat/${project.id}`);
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
