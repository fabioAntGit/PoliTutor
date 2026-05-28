import { z } from "zod";

export const changePasswordSchema = z
  .object({
    current_password: z.string().min(1, "Password atual obrigatória."),
    new_password: z.string().min(8, "A nova password deve ter pelo menos 8 caracteres."),
    confirm_password: z.string().min(1, "Confirma a nova password."),
  })
  .refine((data) => data.new_password === data.confirm_password, {
    path: ["confirm_password"],
    message: "As passwords não coincidem.",
  });

export type ChangePasswordFormValues = z.infer<typeof changePasswordSchema>;
