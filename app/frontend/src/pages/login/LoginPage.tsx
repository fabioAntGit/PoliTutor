import { Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { PasswordInput } from "@/components/password-input";
import { useLogin } from "@/hooks/login/useLogin";

export default function LoginPage() {
  const { form, onSubmit } = useLogin();
  const { register, formState: { errors, isSubmitting } } = form;

  return (
    <main className="min-h-screen flex items-center justify-center p-6 bg-background">
      <form onSubmit={onSubmit} className="w-full max-w-sm space-y-6">
        <div className="space-y-1">
          <h1 className="text-2xl font-semibold tracking-tight text-center">
            Poli Tutor
          </h1>
          <p className="text-sm text-muted-foreground text-center">
            Inicia sessão com as tuas credenciais institucionais.
          </p>
        </div>

        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="username">Username</Label>
            <Input
              id="username"
              placeholder="ist1234567"
              autoComplete="username"
              aria-invalid={!!errors.username}
              {...register("username")}
            />
            {errors.username && (
              <p className="text-xs text-destructive">{errors.username.message}</p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="password">Password</Label>
            <PasswordInput
              id="password"
              autoComplete="current-password"
              aria-invalid={!!errors.password}
              {...register("password")}
            />
            {errors.password && (
              <p className="text-xs text-destructive">{errors.password.message}</p>
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
          {isSubmitting ? <Loader2 className="size-4 animate-spin" /> : "Entrar"}
        </Button>
      </form>
    </main>
  );
}
