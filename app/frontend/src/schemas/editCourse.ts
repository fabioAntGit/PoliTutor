import { z } from "zod";
import { COURSE_NAME_MAX_LENGTH, COURSE_SCOPE_MAX_LENGTH } from "@/lib/validation";

export const editCourseSchema = z.object({
  name: z.string().min(1, "Nome obrigatório.").max(COURSE_NAME_MAX_LENGTH),
  scope: z.string().min(1, "Âmbito obrigatório.").max(COURSE_SCOPE_MAX_LENGTH),
  is_active: z.boolean(),
});

export type EditCourseFormValues = z.infer<typeof editCourseSchema>;
