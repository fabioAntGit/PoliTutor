import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { editUserSchema, type EditUserFormValues } from "@/schemas/editUser";
import { updateUser, deleteUser } from "@/api/users";
import type { UserResponse } from "@/types/user";
import { ApiError } from "@/lib/errors";

export function useEditUser(user: UserResponse | null, onSaved: () => void) {
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const form = useForm<EditUserFormValues>({
    resolver: zodResolver(editUserSchema),
    defaultValues: {
      email: "",
      full_name: "",
      role: "student",
      courses: [],
    },
  });

  useEffect(() => {
    if (user) {
      form.reset({
        email: user.email,
        full_name: user.full_name,
        role: user.role,
        courses: user.courses,
      });
      setDeleteError(null);
    }
  }, [user, form]);

  const onSubmit = async (data: EditUserFormValues) => {
    if (!user) return;
    form.clearErrors("root");
    try {
      await updateUser(user.username, data);
      onSaved();
    } catch (err) {
      const message =
        err instanceof ApiError ? err.message : "Erro ao atualizar utilizador.";
      form.setError("root", { message });
    }
  };

  const onDelete = async () => {
    if (!user) return;
    setDeleteError(null);
    setDeleting(true);
    try {
      await deleteUser(user.username);
      onSaved();
    } catch (err) {
      const message =
        err instanceof ApiError ? err.message : "Erro ao eliminar utilizador.";
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
