import { z } from "zod";

export const createUserSchema = z.object({
  email: z
    .string()
    .email("Email inválido.")
    .refine((email) => email.endsWith("@ipp.pt") || email.endsWith(".ipp.pt"), {
      message: "O email deve pertencer ao domínio ipp.pt.",
    }),
  password: z.string().min(8, "A palavra-passe deve ter pelo menos 8 caracteres."),
  full_name: z.string().min(1, "Nome completo obrigatório."),
  role: z.enum(["student", "teacher"]),
  courses: z.array(z.string()),
});

export type CreateUserFormValues = z.infer<typeof createUserSchema>;
