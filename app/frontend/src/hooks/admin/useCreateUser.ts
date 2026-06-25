import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { createUserSchema, type CreateUserFormValues } from "@/schemas/createUser";
import { UserService } from "@/services/user.service";
import { CourseService } from "@/services/course.service";
import type { CourseResponse } from "@/types/course";
import type { CreatedUserCredentials } from "@/types/user";
import { setFormRootError } from "@/lib/formErrors";

export function useCreateUser() {
  const [courses, setCourses] = useState<CourseResponse[]>([]);
  const [createdUser, setCreatedUser] = useState<CreatedUserCredentials | null>(null);

  useEffect(() => {
    CourseService.listCourses().then(setCourses).catch(() => {});
  }, []);

  const form = useForm<CreateUserFormValues>({
    resolver: zodResolver(createUserSchema),
    defaultValues: {
      email: "",
      password: "",
      full_name: "",
      role: "student",
      courses: [],
    },
  });

  const onSubmit = async (data: CreateUserFormValues) => {
    form.clearErrors("root");
    setCreatedUser(null);
    try {
      const user = await UserService.createUser(data);
      setCreatedUser({ username: user.username, password: data.password });
      form.reset();
    } catch (err) {
      setFormRootError(form, err, "Erro ao criar utilizador. Tenta novamente.");
    }
  };

  const dismissCreatedUser = () => setCreatedUser(null);

  return {
    form,
    courses,
    createdUser,
    dismissCreatedUser,
    onSubmit: form.handleSubmit(onSubmit),
  };
}
