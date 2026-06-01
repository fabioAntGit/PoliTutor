import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { createCourseSchema, type CreateCourseFormValues } from "@/schemas/createCourse";
import { createCourse } from "@/api/courses";
import { setFormRootError } from "@/lib/formErrors";

export function useCreateCourse() {
  const [success, setSuccess] = useState(false);

  const form = useForm<CreateCourseFormValues>({
    resolver: zodResolver(createCourseSchema),
    defaultValues: { code: "", name: "", description: "" },
  });

  const onSubmit = async (data: CreateCourseFormValues) => {
    form.clearErrors("root");
    setSuccess(false);
    try {
      await createCourse(data);
      setSuccess(true);
      form.reset();
    } catch (err) {
      setFormRootError(form, err, "Erro ao criar cadeira. Tenta novamente.");
    }
  };

  return {
    form,
    success,
    onSubmit: form.handleSubmit(onSubmit),
  };
}
