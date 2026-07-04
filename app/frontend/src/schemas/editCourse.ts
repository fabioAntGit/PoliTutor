import { z } from "zod";

export const editCourseSchema = z.object({
  name: z.string().min(1, "Nome obrigatório.").max(255),
  scope: z.string().min(1, "Âmbito obrigatório."),
  is_active: z.boolean(),
});

export type EditCourseFormValues = z.infer<typeof editCourseSchema>;
