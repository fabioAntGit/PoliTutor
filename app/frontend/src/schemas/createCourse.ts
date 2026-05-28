import { z } from "zod";

export const createCourseSchema = z.object({
  code: z.string().min(1, "Código obrigatório.").max(64),
  name: z.string().min(1, "Nome obrigatório.").max(255),
  description: z.string(),
});

export type CreateCourseFormValues = z.infer<typeof createCourseSchema>;
