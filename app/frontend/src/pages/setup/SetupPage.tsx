import { Link } from "react-router";
import { ArrowRight, ArrowLeft, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { PasswordInput } from "@/components/password-input";
import { useSetup } from "@/hooks/setup/useSetup";
import { PageState } from "@/components/ui/page-state";

export default function SetupPage() {
  const { form, onSubmit, hasConfig } = useSetup();
  const { register, formState: { errors, isValid, isSubmitting } } = form;

  return (
    <PageState loading={false}>
      <main className="min-h-screen flex items-center justify-center p-6 bg-background relative">
        {hasConfig && (
          <div className="absolute top-6 left-6">
            <Button variant="ghost" asChild size="sm" className="gap-1">
              <Link to="/">
                <ArrowLeft className="h-4 w-4" />
                Voltar aos Projetos
              </Link>
            </Button>
          </div>
        )}

        <form
          onSubmit={onSubmit}
          className="w-full max-w-xl space-y-8"
        >
          <div className="space-y-1">
            <h1 className="text-2xl font-semibold tracking-tight text-center lg:text-left">
              Configuração Tutor
            </h1>
            <p className="text-sm text-muted-foreground text-center lg:text-left">
              Aceda a{" "}
              <a
                href="https://iaedu.pt"
                target="_blank"
                rel="noopener noreferrer"
                className="font-semibold text-primary underline-offset-4 hover:underline"
              >
                iaedu.pt
              </a>{" "}
              e obtenha as informações necessárias da sua API.
            </p>
          </div>

          <div className="space-y-4">
            <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground border-b pb-2">
              Credenciais IAEdu
            </p>

            <div className="space-y-2">
              <Label htmlFor="endpoint">Endpoint da API</Label>
              <Input
                id="endpoint"
                type="url"
                placeholder="https://api.iaedu.pt/agent-chat//api/v1/agent/{id}/stream"
                aria-invalid={!!errors.endpoint}
                {...register("endpoint")}
              />
              {errors.endpoint ? (
                <p className="text-xs text-destructive">{errors.endpoint.message}</p>
              ) : (
                <p className="text-xs text-muted-foreground">
                  URL do agente IAEdu. Formato: <code>https://api.iaedu.pt/agent-chat//api/v1/agent/&#123;id&#125;/stream</code>
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
            <p className="text-sm text-destructive p-2 bg-destructive/10 rounded-md text-center">
              {errors.root.message}
            </p>
          ) : null}

          <div className="flex flex-col sm:flex-row gap-3">
            <Button
              type="submit"
              size="lg"
              className="flex-1 h-12 text-base font-semibold"
              disabled={!isValid || isSubmitting}
            >
              {isSubmitting ? (
                <Loader2 className="size-4 animate-spin" />
              ) : (
                <>
                  Guardar e Continuar
                  <ArrowRight className="ml-2 size-4" />
                </>
              )}
            </Button>

            {hasConfig && (
              <Button
                type="button"
                variant="outline"
                size="lg"
                asChild
                className="flex-1 h-12 text-base"
              >
                <Link to="/">Continuar sem Guardar</Link>
              </Button>
            )}
          </div>
        </form>
      </main>
    </PageState>
  );
}
