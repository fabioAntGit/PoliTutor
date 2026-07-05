import { ArrowLeft, KeyRound } from "lucide-react";
import { Button } from "@/components/ui/button";
import { FormPasswordField } from "@/components/form/form-password-field";
import { FormRootError } from "@/components/form/form-root-error";
import { SubmitButton } from "@/components/form/submit-button";
import { useChangePassword } from "@/hooks/auth/useChangePassword";

export default function ChangePasswordPage() {
  const { form, onSubmit, mustChange, goBack } = useChangePassword();
  const {
    register,
    formState: { errors, isSubmitting },
  } = form;

  return (
    <main className="relative flex min-h-screen items-center justify-center bg-background p-6">
      {!mustChange && (
        <Button
          variant="ghost"
          size="sm"
          className="absolute left-4 top-4 text-muted-foreground"
          onClick={goBack}
        >
          <ArrowLeft className="size-4" />
          Voltar
        </Button>
      )}

      <div className="w-full max-w-sm rounded-2xl border border-border/70 bg-card/40 p-7 shadow-xl">
        <div className="mb-6 flex flex-col items-center text-center">
          <div className="mb-3 flex size-11 items-center justify-center rounded-2xl bg-primary/10">
            <KeyRound className="size-5 text-primary" />
          </div>
          <h1 className="text-xl font-semibold tracking-tight">
            Alterar palavra-passe
          </h1>
          <p className="mt-1 text-[13px] leading-relaxed text-muted-foreground">
            {mustChange
              ? "Tem de definir uma nova palavra-passe antes de continuar."
              : "Defina uma nova palavra-passe para a sua conta."}
          </p>
        </div>

        <form onSubmit={onSubmit} className="space-y-4">
          <div className="space-y-3">
            <FormPasswordField
              id="current_password"
              label="Palavra-passe atual"
              autoComplete="current-password"
              className="h-11 text-sm"
              error={errors.current_password?.message}
              {...register("current_password")}
            />

            <FormPasswordField
              id="new_password"
              label="Nova palavra-passe"
              autoComplete="new-password"
              className="h-11 text-sm"
              error={errors.new_password?.message}
              {...register("new_password")}
            />

            <FormPasswordField
              id="confirm_password"
              label="Confirmar nova palavra-passe"
              autoComplete="new-password"
              className="h-11 text-sm"
              error={errors.confirm_password?.message}
              {...register("confirm_password")}
            />
          </div>

          <FormRootError message={errors.root?.message} />

          <SubmitButton loading={isSubmitting} className="h-11 text-sm">
            Alterar palavra-passe
          </SubmitButton>
        </form>
      </div>
    </main>
  );
}
