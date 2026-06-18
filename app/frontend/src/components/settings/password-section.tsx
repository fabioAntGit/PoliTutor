import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { toast } from "sonner";

import { FormPasswordField } from "@/components/form/form-password-field";
import { FormRootError } from "@/components/form/form-root-error";
import { SubmitButton } from "@/components/form/submit-button";
import {
  changePasswordSchema,
  type ChangePasswordFormValues,
} from "@/schemas/changePassword";
import { AuthService } from "@/services/auth.service";
import { ApiError } from "@/lib/errors";

export function PasswordSection() {
  const form = useForm<ChangePasswordFormValues>({
    resolver: zodResolver(changePasswordSchema),
    defaultValues: {
      current_password: "",
      new_password: "",
      confirm_password: "",
    },
  });

  const {
    register,
    formState: { errors, isSubmitting },
  } = form;

  const onSubmit = form.handleSubmit(async (data) => {
    form.clearErrors("root");
    try {
      const tokens = await AuthService.changePassword(data.current_password, data.new_password);
      AuthService.setTokens(tokens.access_token);
      toast.success("Palavra-passe alterada com sucesso.");
      form.reset();
    } catch (err) {
      const message =
        err instanceof ApiError ? err.message : "Erro ao alterar a palavra-passe.";
      form.setError("root", { message });
    }
  });

  return (
    <form onSubmit={onSubmit} className="max-w-sm space-y-4">
      <p className="text-[13px] leading-relaxed text-muted-foreground">
        Defina uma nova palavra-passe para a sua conta.
      </p>

      <div className="space-y-3">
        <FormPasswordField
          id="current_password"
          label="Palavra-passe atual"
          autoComplete="current-password"
          className="h-10 text-sm"
          error={errors.current_password?.message}
          {...register("current_password")}
        />

        <FormPasswordField
          id="new_password"
          label="Nova palavra-passe"
          autoComplete="new-password"
          className="h-10 text-sm"
          error={errors.new_password?.message}
          {...register("new_password")}
        />

        <FormPasswordField
          id="confirm_password"
          label="Confirmar nova palavra-passe"
          autoComplete="new-password"
          className="h-10 text-sm"
          error={errors.confirm_password?.message}
          {...register("confirm_password")}
        />
      </div>

      <FormRootError message={errors.root?.message} />

      <SubmitButton
        loading={isSubmitting}
        className="h-10 w-auto px-5 text-sm"
      >
        Alterar palavra-passe
      </SubmitButton>
    </form>
  );
}
