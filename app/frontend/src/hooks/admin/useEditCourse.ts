import { editCourseSchema, type EditCourseFormValues } from "@/schemas/editCourse";
import { updateCourse, deleteCourse } from "@/api/courses";
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
    update: (c, data) => updateCourse(c.code, data),
    remove: (c) => deleteCourse(c.code),
    updateErrorMessage: "Erro ao atualizar cadeira.",
    deleteErrorMessage: "Erro ao eliminar cadeira.",
  });
}
