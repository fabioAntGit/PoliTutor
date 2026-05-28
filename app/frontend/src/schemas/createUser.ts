import { z } from "zod";

export const createUserSchema = z.object({
  email: z
    .email("Email inválido.")
    .endsWith("@estg.ipp.pt", "O email deve pertencer ao domínio @estg.ipp.pt."),
  password: z.string().min(8, "Password deve ter pelo menos 8 caracteres."),
  full_name: z.string().min(1, "Nome completo obrigatório."),
  role: z.enum(["student", "teacher"]),
  courses: z.array(z.string()),
});

export type CreateUserFormValues = z.infer<typeof createUserSchema>;
