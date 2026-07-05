import { z } from "zod";
import { COURSE_CODE_MAX_LENGTH, COURSE_NAME_MAX_LENGTH, COURSE_SCOPE_MAX_LENGTH } from "@/lib/validation";

export const createCourseSchema = z.object({
  code: z.string().min(1, "Código obrigatório.").max(COURSE_CODE_MAX_LENGTH),
  name: z.string().min(1, "Nome obrigatório.").max(COURSE_NAME_MAX_LENGTH),
  scope: z.string().min(1, "Âmbito obrigatório.").max(COURSE_SCOPE_MAX_LENGTH),
});

export type CreateCourseFormValues = z.infer<typeof createCourseSchema>;
