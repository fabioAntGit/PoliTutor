import { useEffect, useState } from "react";
import { useForm, type DefaultValues, type FieldValues } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import type { ZodType } from "zod";
import { ApiError } from "@/lib/errors";
import { setFormRootError } from "@/lib/formErrors";

export function useEntityEditForm<TEntity, TForm extends FieldValues>({
  entity,
  onSaved,
  schema,
  defaultValues,
  toFormValues,
  update,
  remove,
  updateErrorMessage,
  deleteErrorMessage,
}: {
  entity: TEntity | null;
  onSaved: () => void;
  schema: ZodType<TForm>;
  defaultValues: DefaultValues<TForm>;
  toFormValues: (entity: TEntity) => TForm;
  update: (entity: TEntity, data: TForm) => Promise<unknown>;
  remove: (entity: TEntity) => Promise<unknown>;
  updateErrorMessage: string;
  deleteErrorMessage: string;
}) {
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const form = useForm<TForm>({
    resolver: zodResolver(schema),
    defaultValues,
  });

  useEffect(() => {
    if (entity) {
      form.reset(toFormValues(entity));
      setDeleteError(null);
    }
  }, [entity, form]);

  const onSubmit = async (data: TForm) => {
    if (!entity) return;
    form.clearErrors("root");
    try {
      await update(entity, data);
      onSaved();
    } catch (err) {
      setFormRootError(form, err, updateErrorMessage);
    }
  };

  const onDelete = async () => {
    if (!entity) return;
    setDeleteError(null);
    setDeleting(true);
    try {
      await remove(entity);
      onSaved();
    } catch (err) {
      setDeleteError(err instanceof ApiError ? err.message : deleteErrorMessage);
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
