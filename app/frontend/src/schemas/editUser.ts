import { z } from "zod";

export const editUserSchema = z.object({
  email: z
    .email("Email inválido.")
    .endsWith("@estg.ipp.pt", "O email deve pertencer ao domínio @estg.ipp.pt."),
  full_name: z.string().min(1, "Nome completo obrigatório."),
  role: z.enum(["student", "teacher", "admin"]),
  courses: z.array(z.string()),
});

export type EditUserFormValues = z.infer<typeof editUserSchema>;
