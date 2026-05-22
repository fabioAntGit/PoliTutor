import { ArrowLeft } from "lucide-react";
import { useNavigate } from "react-router";
import { Button } from "@/components/ui/button";
import { FormPasswordField } from "@/components/form/FormPasswordField";
import { FormRootError } from "@/components/form/FormRootError";
import { SubmitButton } from "@/components/form/SubmitButton";
import { useChangePassword } from "@/hooks/auth/useChangePassword";
import { authService } from "@/services/auth.service";

export default function ChangePasswordPage() {
  const navigate = useNavigate();
  const { form, onSubmit } = useChangePassword();
  const {
    register,
    formState: { errors, isSubmitting },
  } = form;

  const mustChange = authService.mustChangePassword();

  return (
    <main className="min-h-screen flex items-center justify-center p-6 bg-background relative">
      {!mustChange && (
        <div className="absolute top-6 left-6">
          <Button
            variant="ghost"
            size="icon"
            title="Voltar"
            onClick={() => navigate(-1)}
          >
            <ArrowLeft className="h-5 w-5 text-muted-foreground hover:text-primary transition-colors" />
          </Button>
        </div>
      )}
      <form onSubmit={onSubmit} className="w-full max-w-sm space-y-6">
        <div className="space-y-1">
          <h1 className="text-2xl font-semibold tracking-tight text-center">
            Alterar password
          </h1>
          <p className="text-sm text-muted-foreground text-center">
            Tens de definir uma password nova antes de continuar.
          </p>
        </div>

        <div className="space-y-4">
          <FormPasswordField
            id="current_password"
            label="Password atual"
            autoComplete="current-password"
            error={errors.current_password?.message}
            {...register("current_password")}
          />

          <FormPasswordField
            id="new_password"
            label="Nova password"
            autoComplete="new-password"
            error={errors.new_password?.message}
            {...register("new_password")}
          />

          <FormPasswordField
            id="confirm_password"
            label="Confirmar nova password"
            autoComplete="new-password"
            error={errors.confirm_password?.message}
            {...register("confirm_password")}
          />
        </div>

        <FormRootError message={errors.root?.message} />

        <SubmitButton loading={isSubmitting}>Alterar password</SubmitButton>
      </form>
    </main>
  );
}
