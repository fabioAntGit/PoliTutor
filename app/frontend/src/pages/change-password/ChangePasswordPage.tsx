import { ArrowLeft, Loader2 } from "lucide-react";
import { useNavigate } from "react-router";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { PasswordInput } from "@/components/password-input";
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
          <div className="space-y-2">
            <Label htmlFor="current_password">Password atual</Label>
            <PasswordInput
              id="current_password"
              autoComplete="current-password"
              aria-invalid={!!errors.current_password}
              {...register("current_password")}
            />
            {errors.current_password && (
              <p className="text-xs text-destructive">{errors.current_password.message}</p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="new_password">Nova password</Label>
            <PasswordInput
              id="new_password"
              autoComplete="new-password"
              aria-invalid={!!errors.new_password}
              {...register("new_password")}
            />
            {errors.new_password && (
              <p className="text-xs text-destructive">{errors.new_password.message}</p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="confirm_password">Confirmar nova password</Label>
            <PasswordInput
              id="confirm_password"
              autoComplete="new-password"
              aria-invalid={!!errors.confirm_password}
              {...register("confirm_password")}
            />
            {errors.confirm_password && (
              <p className="text-xs text-destructive">{errors.confirm_password.message}</p>
            )}
          </div>
        </div>

        {errors.root && (
          <p className="text-sm text-destructive p-2 bg-destructive/10 rounded-md text-center">
            {errors.root.message}
          </p>
        )}

        <Button
          type="submit"
          size="lg"
          className="w-full h-12 text-base font-semibold"
          disabled={isSubmitting}
        >
          {isSubmitting ? <Loader2 className="size-4 animate-spin" /> : "Alterar password"}
        </Button>
      </form>
    </main>
  );
}
