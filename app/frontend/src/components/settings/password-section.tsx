import { toast } from "sonner";

import { FormPasswordField } from "@/components/form/form-password-field";
import { FormRootError } from "@/components/form/form-root-error";
import { SubmitButton } from "@/components/form/submit-button";
import { useChangePassword } from "@/hooks/auth/useChangePassword";

export function PasswordSection() {
  const { form, onSubmit } = useChangePassword({
    onSuccess: () => toast.success("Palavra-passe alterada com sucesso."),
  });

  const {
    register,
    formState: { errors, isSubmitting },
  } = form;

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
