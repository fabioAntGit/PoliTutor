import { z } from "zod";

export const editUserSchema = z.object({
  email: z
    .string()
    .email("Email inválido.")
    .refine((email) => email.endsWith("@ipp.pt") || email.endsWith(".ipp.pt"), {
      message: "O email deve pertencer ao domínio ipp.pt.",
    }),
  full_name: z.string().min(1, "Nome completo obrigatório."),
  role: z.enum(["student", "teacher"]),
  courses: z.array(z.string()),
});

export type EditUserFormValues = z.infer<typeof editUserSchema>;
