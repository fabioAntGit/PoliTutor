import axios from "axios";
import { useNavigate } from "react-router";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { loginSchema, type LoginFormValues } from "@/schemas/login";
import { login } from "@/api/auth";
import { authService } from "@/services/auth.service";
import { landingForRole } from "@/lib/landing";

export function useLogin() {
  const navigate = useNavigate();

  const form = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    mode: "onBlur",
  });

  const onSubmit = async (data: LoginFormValues) => {
    form.clearErrors("root");
    try {
      const tokens = await login(data.username, data.password);
      authService.setTokens(tokens.access_token);
      navigate(landingForRole(authService.getRole()), { replace: true });
    } catch (err) {
      let message = "Erro ao autenticar. Tenta novamente.";
      if (axios.isAxiosError(err)) {
        message = err.response?.data?.detail ?? message;
      }
      form.setError("root", { message });
    }
  };

  return {
    form,
    onSubmit: form.handleSubmit(onSubmit),
  };
}
