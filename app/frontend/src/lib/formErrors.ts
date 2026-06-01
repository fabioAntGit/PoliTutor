import type { FieldValues, UseFormReturn } from "react-hook-form";
import { ApiError } from "@/lib/errors";

export function setFormRootError<T extends FieldValues>(
  form: UseFormReturn<T>,
  err: unknown,
  fallback: string,
) {
  const message = err instanceof ApiError ? err.message : fallback;
  form.setError("root", { message });
}
