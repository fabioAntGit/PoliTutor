import { useState } from "react";
import { Eye, EyeOff } from "lucide-react";
import { FormRootError } from "@/components/form/FormRootError";
import { SubmitButton } from "@/components/form/SubmitButton";
import { Input } from "@/components/ui/input";
import { ThemeToggle } from "@/components/theme/theme-toggle";
import { useLogin } from "@/hooks/login/useLogin";
import poliTutorImg from "/poli_tutor_question.png";

const inputClass =
  "h-12 rounded-xl bg-white px-4 text-[15px] text-[#1d1d1d] border-[rgba(29,29,29,0.18)] placeholder:text-[rgba(29,29,29,0.45)] focus-visible:border-[#1d1d1d] focus-visible:ring-0 dark:bg-input/30 dark:text-foreground dark:border-input dark:placeholder:text-muted-foreground dark:focus-visible:border-ring";

export default function LoginPage() {
  const { form, onSubmit } = useLogin();
  const { register, formState: { errors, isSubmitting, isValid } } = form;
  const [showPassword, setShowPassword] = useState(false);

  return (
    <main className="relative flex min-h-screen w-full bg-background">
      <div className="absolute right-4 top-4 z-20">
        <ThemeToggle />
      </div>
      <section className="relative hidden overflow-hidden border-r border-white/5 lg:block lg:w-1/2">
        <img
          src={poliTutorImg}
          alt="Poli Tutor"
          className="absolute inset-0 h-full w-full object-cover"
        />
      </section>
      <section className="flex w-full flex-col bg-white text-[#1d1d1d] dark:bg-background dark:text-foreground lg:w-1/2">
        <div className="flex flex-1 items-center justify-center px-6 py-10 sm:px-10">
          <div className="w-full max-w-[380px]">
            <h1 className="text-[26px] font-semibold leading-tight tracking-tight text-[#1d1d1d] dark:text-foreground">
              Aceder à conta
            </h1>
            <p className="mt-2 text-sm leading-relaxed text-[rgba(29,29,29,0.65)] dark:text-muted-foreground">
              Introduza as suas credenciais institucionais para continuar.
            </p>

            <form onSubmit={onSubmit} className="mt-6 space-y-3">
              <div className="space-y-1.5">
                <Input
                  id="username"
                  placeholder="Username"
                  autoComplete="username"
                  aria-label="Username"
                  aria-invalid={!!errors.username}
                  className={inputClass}
                  {...register("username")}
                />
                {errors.username && (
                  <p className="px-1 text-xs text-destructive">{errors.username.message}</p>
                )}
              </div>

              <div className="space-y-1.5">
                <div className="relative">
                  <Input
                    id="password"
                    type={showPassword ? "text" : "password"}
                    placeholder="Password"
                    autoComplete="current-password"
                    aria-label="Password"
                    aria-invalid={!!errors.password}
                    className={`${inputClass} pr-11`}
                    {...register("password")}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword((v) => !v)}
                    aria-label={showPassword ? "Esconder password" : "Mostrar password"}
                    tabIndex={-1}
                    className="absolute right-0 top-0 flex h-full items-center justify-center px-3.5 text-[rgba(29,29,29,0.5)] transition-colors hover:text-[#1d1d1d] dark:text-muted-foreground dark:hover:text-foreground"
                  >
                    {showPassword ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
                  </button>
                </div>
                {errors.password && (
                  <p className="px-1 text-xs text-destructive">{errors.password.message}</p>
                )}
              </div>

              <FormRootError message={errors.root?.message} />

              <SubmitButton
                loading={isSubmitting}
                disabled={!isValid}
                className="mt-3 h-12 rounded-xl bg-[#1d1d1d] text-white hover:bg-[#1d1d1d]/90 disabled:bg-[rgba(29,29,29,0.35)] disabled:text-white disabled:opacity-100 dark:bg-foreground dark:text-background dark:hover:bg-foreground/90 dark:disabled:bg-foreground/35 dark:disabled:text-background"
              >
                Entrar
              </SubmitButton>
            </form>
          </div>
        </div>
      </section>
    </main>
  );
}