import { useForm } from "react-hook-form";
import { useNavigate } from "react-router";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  changePasswordSchema,
  type ChangePasswordFormValues,
} from "@/schemas/changePassword";
import { changePassword } from "@/api/auth";
import { authService } from "@/services/auth.service";
import { ApiError } from "@/lib/errors";

export function useChangePassword() {
  const navigate = useNavigate();

  const form = useForm<ChangePasswordFormValues>({
    resolver: zodResolver(changePasswordSchema),
    defaultValues: { current_password: "", new_password: "", confirm_password: "" },
  });

  const onSubmit = async (data: ChangePasswordFormValues) => {
    form.clearErrors("root");
    try {
      const tokens = await changePassword(data.current_password, data.new_password);
      authService.setTokens(tokens.access_token);
      navigate("/", { replace: true });
    } catch (err) {
      const message =
        err instanceof ApiError ? err.message : "Erro ao alterar password.";
      form.setError("root", { message });
    }
  };

  return { form, onSubmit: form.handleSubmit(onSubmit) };
}
