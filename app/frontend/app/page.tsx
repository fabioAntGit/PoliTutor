"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { ArrowRight, Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { PasswordInput } from "@/components/password-input";
import { ProjectCard } from "@/components/project-card";
import { PROJECTS } from "@/constants/projects";
import { setupSchema, type SetupFormValues } from "@/lib/schemas/setup";
import { saveConfig } from "@/lib/session-config";

export default function Home() {
  const router = useRouter();

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors, isValid, isSubmitting },
  } = useForm<SetupFormValues>({
    resolver: zodResolver(setupSchema),
    mode: "onBlur",
  });

  const selectedProjectId = watch("projectId");

  // Auto-select if there's only one project
  useEffect(() => {
    if (PROJECTS.length === 1) {
      setValue("projectId", PROJECTS[0].id, { shouldValidate: true });
    }
  }, [setValue]);

  function onSubmit(data: SetupFormValues) {
    saveConfig(data);
    router.push(`/chat/${data.projectId}`);
  }

  return (
    <main className="min-h-screen flex items-center justify-center p-6">
      <form
        onSubmit={handleSubmit(onSubmit)}
        className="w-full max-w-xl space-y-8"
      >
        {/* Header */}
        <div className="space-y-1">
          <h1 className="text-2xl font-semibold tracking-tight">Poli Tutor</h1>
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

        {/* Project selection */}
        <div className="space-y-3">
          <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
            Projeto
          </p>
          {errors.projectId && (
            <p className="text-xs text-destructive">{errors.projectId.message}</p>
          )}
          <div className="grid gap-3">
            {PROJECTS.map((project) => (
              <ProjectCard
                key={project.id}
                project={project}
                selected={selectedProjectId === project.id}
                onSelect={(p) =>
                  setValue("projectId", p.id, { shouldValidate: true })
                }
              />
            ))}
          </div>
        </div>

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
  );
}