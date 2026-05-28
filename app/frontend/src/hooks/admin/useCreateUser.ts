import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { createUserSchema, type CreateUserFormValues } from "@/schemas/createUser";
import { createUser } from "@/api/users";
import { listCourses } from "@/api/courses";
import type { CourseResponse } from "@/types/course";
import { ApiError } from "@/lib/errors";

export interface CreatedUserCredentials {
  username: string;
  password: string;
}

export function useCreateUser() {
  const [courses, setCourses] = useState<CourseResponse[]>([]);
  const [createdUser, setCreatedUser] = useState<CreatedUserCredentials | null>(null);

  useEffect(() => {
    listCourses().then(setCourses).catch(() => {});
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
      const user = await createUser(data);
      setCreatedUser({ username: user.username, password: data.password });
      form.reset();
    } catch (err) {
      const message =
        err instanceof ApiError
          ? err.message
          : "Erro ao criar utilizador. Tenta novamente.";
      form.setError("root", { message });
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
