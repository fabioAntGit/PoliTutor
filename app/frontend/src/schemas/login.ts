import { z } from "zod";

export const loginSchema = z.object({
  username: z.string().min(1, "Username obrigatório."),
  password: z.string().min(1, "Password obrigatória."),
});

export type LoginFormValues = z.infer<typeof loginSchema>;
