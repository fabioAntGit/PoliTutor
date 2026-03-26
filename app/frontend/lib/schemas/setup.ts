import { z } from "zod";

export const setupSchema = z.object({
  endpoint: z
    .string()
    .min(1, "O endpoint é obrigatório.")
    .url("Introduza um URL válido.")
    .refine((val) => val.startsWith("https://"), "O endpoint deve usar HTTPS.")
    .refine((val) => val.endsWith("/stream"), "O endpoint deve terminar em /stream."),

  apiKey: z
    .string()
    .min(1, "A chave de API é obrigatória.")
    .regex(/^sk-usr-[a-z0-9]+$/, "Formato inválido. Exemplo: sk-usr-olzgh5hx4bjwrq7ggqkxxqd31x"),

  channelId: z
    .string()
    .min(1, "O ID do canal é obrigatório.")
    .regex(/^[a-z0-9]+$/, "O ID do canal só pode conter letras minúsculas e números.")
    .min(10, "O ID do canal parece demasiado curto."),

  projectId: z.string().min(1, "Selecione um projeto."),
});

export type SetupFormValues = z.infer<typeof setupSchema>;