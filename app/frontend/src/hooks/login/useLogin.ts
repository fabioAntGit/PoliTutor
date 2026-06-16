import { useNavigate } from "react-router";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { loginSchema, type LoginFormValues } from "@/schemas/login";
import { ApiError } from "@/lib/errors";
import { authService } from "@/services/auth.service";
import { landingForRole } from "@/lib/landing";

export function useLogin() {
  const navigate = useNavigate();

  const form = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    mode: "onChange",
  });

  const onSubmit = async (data: LoginFormValues) => {
    form.clearErrors("root");
    try {
      const tokens = await authService.login(data.username, data.password);
      authService.setTokens(tokens.access_token);
      navigate(landingForRole(authService.getRole()), { replace: true });
    } catch (err) {
      const message =
        err instanceof ApiError ? err.message : "Erro ao autenticar. Tenta novamente.";
      form.setError("root", { message });
    }
  };

  return {
    form,
    onSubmit: form.handleSubmit(onSubmit),
  };
}
