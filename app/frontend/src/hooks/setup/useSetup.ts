import { useNavigate } from "react-router";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { setupSchema, type SetupFormValues } from "@/schemas/setup";
import { sessionService } from "@/services/session.service";
import { useEffect, useState } from "react";

export function useSetup() {
  const navigate = useNavigate();
  const [hasConfig, setHasConfig] = useState(false);

  const form = useForm<SetupFormValues>({
    resolver: zodResolver(setupSchema),
    mode: "onBlur",
  });

  useEffect(() => {
    const config = sessionService.loadConfig();
    if (config) {
      setHasConfig(true);
      form.reset({
        endpoint: config.endpoint,
        apiKey: config.apiKey,
        channelId: config.channelId,
      });
    }
  }, [form]);

  const onSubmit = async (data: SetupFormValues) => {
    form.clearErrors("root");

    try {
      sessionService.saveConfig(data);
      navigate("/", { replace: true });
    } catch (error) {
      form.setError("root", {
        message: error instanceof Error ? error.message : "Erro ao guardar configuração.",
      });
    }
  };

  return {
    form,
    hasConfig,
    onSubmit: form.handleSubmit(onSubmit),
  };
}
