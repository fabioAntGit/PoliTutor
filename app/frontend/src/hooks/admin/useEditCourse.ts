import { editCourseSchema, type EditCourseFormValues } from "@/schemas/editCourse";
import { CourseService } from "@/services/course.service";
import type { CourseResponse } from "@/types/course";
import { useEntityEditForm } from "@/hooks/admin/useEntityEditForm";

export function useEditCourse(course: CourseResponse | null, onSaved: () => void) {
  return useEntityEditForm<CourseResponse, EditCourseFormValues>({
    entity: course,
    onSaved,
    schema: editCourseSchema,
    defaultValues: { name: "", description: "", is_active: true },
    toFormValues: (c) => ({
      name: c.name,
      description: c.description,
      is_active: c.is_active,
    }),
    update: (c, data) => CourseService.updateCourse(c.code, data),
    remove: (c) => CourseService.deleteCourse(c.code),
    updateErrorMessage: "Erro ao atualizar cadeira.",
    deleteErrorMessage: "Erro ao eliminar cadeira.",
  });
}
