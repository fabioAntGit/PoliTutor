import { Link } from "react-router";
import { ArrowLeft, ArrowRight, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { PasswordInput } from "@/components/password-input";
import { useSetup } from "@/hooks/setup/useSetup";
import { PageState } from "@/components/ui/page-state";

export default function SetupPage() {
  const { project, loading, error, form, onSubmit } = useSetup();
  const { register, formState: { errors, isValid, isSubmitting } } = form;

  return (
    <PageState loading={loading} error={error}>
      <main className="min-h-screen flex items-center justify-center p-6">
      <form
        onSubmit={onSubmit}
        className="w-full max-w-xl space-y-8"
      >
        {/* Header */}
        <div className="space-y-1">
          <Link
            to="/"
            className="mb-2 inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground"
          >
            <ArrowLeft className="size-3" />
            Projetos
          </Link>
          <h1 className="text-2xl font-semibold tracking-tight">{project?.name}</h1>
          <p className="text-sm text-muted-foreground">
            Aceda a{" "}
            <a
              href="https://iaedu.pt"
              target="_blank"
              rel="noopener noreferrer"
              className="font-semibold text-primary underline-offset-4 hover:underline"
            >
              iaedu.pt
            </a>{" "}
            e obtenha as informações necessárias da API do GPT-4o.
          </p>
        </div>

        {/* IAEdu credentials */}
        <div className="space-y-4">
          <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
            Credenciais IAEdu
          </p>

          <div className="space-y-2">
            <Label htmlFor="endpoint">Endpoint da API</Label>
            <Input
              id="endpoint"
              type="url"
              placeholder="https://api.iaedu.pt/…/stream"
              aria-invalid={!!errors.endpoint}
              {...register("endpoint")}
            />
            {errors.endpoint ? (
              <p className="text-xs text-destructive">{errors.endpoint.message}</p>
            ) : (
              <p className="text-xs text-muted-foreground">
                URL do agente IAEdu, termina em <code>/stream</code>.
              </p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="apiKey">Chave de API</Label>
            <PasswordInput
              id="apiKey"
              placeholder="sk-usr-…"
              aria-invalid={!!errors.apiKey}
              {...register("apiKey")}
            />
            {errors.apiKey ? (
              <p className="text-xs text-destructive">{errors.apiKey.message}</p>
            ) : (
              <p className="text-xs text-muted-foreground">
                Começa sempre com <code>sk-usr-</code>.
              </p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="channelId">ID do Canal</Label>
            <Input
              id="channelId"
              placeholder="cml0z1jd22dt2gd01fvzw8013"
              aria-invalid={!!errors.channelId}
              {...register("channelId")}
            />
            {errors.channelId ? (
              <p className="text-xs text-destructive">{errors.channelId.message}</p>
            ) : (
              <p className="text-xs text-muted-foreground">
                Identificador do canal associado ao agente.
              </p>
            )}
          </div>
        </div>

        {errors.root ? (
          <p className="text-sm text-destructive">{errors.root.message}</p>
        ) : null}

        <Button
          type="submit"
          size="lg"
          variant="outline"
          className="w-full h-12 text-base font-semibold"
          disabled={!isValid || isSubmitting}
        >
          {isSubmitting ? (
            <Loader2 className="size-4 animate-spin" />
          ) : (
            <>
              Continuar
              <ArrowRight className="ml-1 size-4" />
            </>
          )}
        </Button>
      </form>
    </main>
    </PageState>
  );
}
