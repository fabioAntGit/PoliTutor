import { FormField } from "@/components/form/FormField";
import { FormPasswordField } from "@/components/form/FormPasswordField";
import { FormRootError } from "@/components/form/FormRootError";
import { SubmitButton } from "@/components/form/SubmitButton";
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
          <FormField
            id="username"
            label="Username"
            placeholder="ist1234567"
            autoComplete="username"
            error={errors.username?.message}
            {...register("username")}
          />

          <FormPasswordField
            id="password"
            label="Password"
            autoComplete="current-password"
            error={errors.password?.message}
            {...register("password")}
          />
        </div>

        <FormRootError message={errors.root?.message} />

        <SubmitButton loading={isSubmitting}>Entrar</SubmitButton>
      </form>
    </main>
  );
}
