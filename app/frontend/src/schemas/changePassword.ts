import { z } from "zod";
import { PASSWORD_MIN_LENGTH } from "@/lib/validation";

export const changePasswordSchema = z
  .object({
    current_password: z.string().min(1, "Password atual obrigatória."),
    new_password: z.string().min(PASSWORD_MIN_LENGTH, `A nova password deve ter pelo menos ${PASSWORD_MIN_LENGTH} caracteres.`),
    confirm_password: z.string().min(1, "Confirma a nova password."),
  })
  .refine((data) => data.new_password === data.confirm_password, {
    path: ["confirm_password"],
    message: "As passwords não coincidem.",
  });

export type ChangePasswordFormValues = z.infer<typeof changePasswordSchema>;
