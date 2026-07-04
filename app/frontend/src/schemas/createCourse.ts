import { z } from "zod";

export const createCourseSchema = z.object({
  code: z.string().min(1, "Código obrigatório.").max(64),
  name: z.string().min(1, "Nome obrigatório.").max(255),
  scope: z.string().min(1, "Âmbito obrigatório."),
});

export type CreateCourseFormValues = z.infer<typeof createCourseSchema>;
