import { editUserSchema, type EditUserFormValues } from "@/schemas/editUser";
import { updateUser, deleteUser } from "@/api/users";
import type { UserResponse } from "@/types/user";
import { useEntityEditForm } from "@/hooks/admin/useEntityEditForm";

export function useEditUser(user: UserResponse | null, onSaved: () => void) {
  return useEntityEditForm<UserResponse, EditUserFormValues>({
    entity: user,
    onSaved,
    schema: editUserSchema,
    defaultValues: { email: "", full_name: "", role: "student", courses: [] },
    toFormValues: (u) => ({
      email: u.email,
      full_name: u.full_name,
      role: u.role as EditUserFormValues["role"],
      courses: u.courses,
    }),
    update: (u, data) => updateUser(u.username, data),
    remove: (u) => deleteUser(u.username),
    updateErrorMessage: "Erro ao atualizar utilizador.",
    deleteErrorMessage: "Erro ao eliminar utilizador.",
  });
}
