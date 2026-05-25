import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { editCourseSchema, type EditCourseFormValues } from "@/schemas/editCourse";
import { updateCourse, deleteCourse } from "@/api/courses";
import type { CourseResponse } from "@/types/course";
import { ApiError } from "@/lib/errors";

export function useEditCourse(course: CourseResponse | null, onSaved: () => void) {
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const form = useForm<EditCourseFormValues>({
    resolver: zodResolver(editCourseSchema),
    defaultValues: { name: "", description: "", is_active: true },
  });

  useEffect(() => {
    if (course) {
      form.reset({
        name: course.name,
        description: course.description,
        is_active: course.is_active,
      });
      setDeleteError(null);
    }
  }, [course, form]);

  const onSubmit = async (data: EditCourseFormValues) => {
    if (!course) return;
    form.clearErrors("root");
    try {
      await updateCourse(course.code, data);
      onSaved();
    } catch (err) {
      const message =
        err instanceof ApiError ? err.message : "Erro ao atualizar cadeira.";
      form.setError("root", { message });
    }
  };

  const onDelete = async () => {
    if (!course) return;
    setDeleteError(null);
    setDeleting(true);
    try {
      await deleteCourse(course.code);
      onSaved();
    } catch (err) {
      const message =
        err instanceof ApiError ? err.message : "Erro ao eliminar cadeira.";
      setDeleteError(message);
    } finally {
      setDeleting(false);
    }
  };

  return {
    form,
    onSubmit: form.handleSubmit(onSubmit),
    onDelete,
    deleting,
    deleteError,
  };
}
