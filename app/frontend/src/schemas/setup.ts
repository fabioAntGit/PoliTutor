import { z } from "zod";

export const setupSchema = z.object({
  endpoint: z
    .string()
    .min(1, "O endpoint e obrigatorio.")
    .regex(
      /^https:\/\/api\.iaedu\.pt\/agent-chat\/\/api\/v1\/agent\/[^/]+\/stream$/,
      "Formato invalido. Exemplo: https://api.iaedu.pt/agent-chat//api/v1/agent/{id}/stream"
    ),

  apiKey: z
    .string()
    .min(1, "A chave de API e obrigatoria.")
    .regex(/^sk-usr-[a-z0-9]+$/, "Formato invalido. Exemplo: sk-usr-olzgh5hx4bjwrq7ggqkxxqd31x"),

  channelId: z
    .string()
    .min(1, "O ID do canal e obrigatorio.")
    .regex(/^[a-z0-9]+$/, "O ID do canal so pode conter letras minusculas e numeros.")
    .min(10, "O ID do canal parece demasiado curto."),
});

export type SetupFormValues = z.infer<typeof setupSchema>;
