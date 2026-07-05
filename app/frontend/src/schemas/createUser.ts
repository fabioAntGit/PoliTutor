import { z } from "zod";
import { PASSWORD_MIN_LENGTH, USER_TEXT_MAX_LENGTH } from "@/lib/validation";

export const createUserSchema = z.object({
  email: z
    .string()
    .max(USER_TEXT_MAX_LENGTH)
    .email("Email inválido.")
    .refine((email) => email.endsWith("@ipp.pt") || email.endsWith(".ipp.pt"), {
      message: "O email deve pertencer ao domínio ipp.pt.",
    }),
  password: z.string().min(PASSWORD_MIN_LENGTH, `A palavra-passe deve ter pelo menos ${PASSWORD_MIN_LENGTH} caracteres.`),
  full_name: z.string().min(1, "Nome completo obrigatório.").max(USER_TEXT_MAX_LENGTH),
  role: z.enum(["student", "teacher"]),
  courses: z.array(z.string()),
});

export type CreateUserFormValues = z.infer<typeof createUserSchema>;
