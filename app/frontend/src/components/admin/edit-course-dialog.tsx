import { useState, useEffect } from "react";
import { Controller } from "react-hook-form";
import { Dialog as DialogPrimitive } from "radix-ui";
import { Loader2, Trash2, AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { FormField } from "@/components/form/form-field";
import { FormRootError } from "@/components/form/form-root-error";
import { useEditCourse } from "@/hooks/admin/useEditCourse";
import type { CourseResponse } from "@/types/course";

interface EditCourseDialogProps {
  course: CourseResponse | null;
  onClose: () => void;
  onSaved: () => void;
}

export default function EditCourseDialog({ course, onClose, onSaved }: EditCourseDialogProps) {
  const { form, onSubmit, onDelete, deleting, deleteError } = useEditCourse(course, onSaved);
  const [confirmDelete, setConfirmDelete] = useState(false);

  const {
    register,
    control,
    formState: { errors, isSubmitting },
  } = form;

  useEffect(() => {
    if (!course) setConfirmDelete(false);
  }, [course]);

  return (
    <DialogPrimitive.Root open={!!course} onOpenChange={(open) => !open && onClose()}>
      <DialogPrimitive.Portal>
        <DialogPrimitive.Overlay className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm" />
        <DialogPrimitive.Content className="fixed left-1/2 top-1/2 z-50 w-full max-w-md -translate-x-1/2 -translate-y-1/2 rounded-lg border bg-background p-6 shadow-lg max-h-[90vh] overflow-y-auto">
          <DialogPrimitive.Title className="text-lg font-semibold">
            Editar cadeira
          </DialogPrimitive.Title>
          <DialogPrimitive.Description className="text-sm text-muted-foreground mb-4 font-mono uppercase">
            {course?.code}
          </DialogPrimitive.Description>

          <form onSubmit={onSubmit} className="space-y-4">
            <FormField
              id="edit-course-name"
              label="Nome"
              error={errors.name?.message}
              {...register("name")}
            />

            <FormField
              id="edit-course-scope"
              label="Âmbito"
              error={errors.scope?.message}
              {...register("scope")}
            />

            <Controller
              name="is_active"
              control={control}
              render={({ field }) => (
                <div className="flex items-start justify-between gap-3 rounded-md border p-3">
                  <div className="space-y-0.5">
                    <Label htmlFor="edit-course-active">Cadeira ativa</Label>
                    <p className="text-xs text-muted-foreground">
                      Quando inativa, ninguém pode criar novos chats nem aceder ao
                      dashboard desta cadeira.
                    </p>
                  </div>

                  <button
                    id="edit-course-active"
                    type="button"
                    role="switch"
                    aria-checked={field.value}
                    onClick={() => field.onChange(!field.value)}
                    className={`relative inline-flex h-5 w-9 shrink-0 cursor-pointer items-center rounded-full transition-colors mt-1 ${
                      field.value ? "bg-primary" : "bg-muted-foreground/30"
                    }`}
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-background transition-transform ${
                        field.value ? "translate-x-4" : "translate-x-0.5"
                      }`}
                    />
                  </button>
                </div>
              )}
            />

            <FormRootError message={errors.root?.message} />

            <div className="flex gap-2 pt-2">
              <Button type="button" variant="outline" className="flex-1" onClick={onClose}>
                Cancelar
              </Button>
              <Button type="submit" className="flex-1" disabled={isSubmitting}>
                {isSubmitting ? <Loader2 className="size-4 animate-spin" /> : "Guardar"}
              </Button>
            </div>
          </form>

          {course && (
            <div className="mt-6 pt-4 border-t">
              {!confirmDelete ? (
                <Button
                  type="button"
                  variant="ghost"
                  className="w-full text-destructive hover:bg-destructive/10 hover:text-destructive"
                  onClick={() => setConfirmDelete(true)}
                >
                  <Trash2 className="size-4 mr-2" />
                  Eliminar cadeira
                </Button>
              ) : (
                <div className="space-y-3 p-3 bg-destructive/5 border border-destructive/20 rounded-md">
                  <div className="flex items-start gap-2">
                    <AlertTriangle className="size-4 text-destructive flex-shrink-0 mt-0.5" />
                    <p className="text-sm">
                      Tens a certeza? A cadeira <strong>{course.code}</strong> será
                      eliminada permanentemente. Só é possível eliminar se não houver
                      utilizadores associados.
                    </p>
                  </div>
                  {deleteError && (
                    <p className="text-xs text-destructive">{deleteError}</p>
                  )}
                  <div className="flex gap-2">
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      className="flex-1"
                      onClick={() => setConfirmDelete(false)}
                      disabled={deleting}
                    >
                      Cancelar
                    </Button>
                    <Button
                      type="button"
                      variant="destructive"
                      size="sm"
                      className="flex-1"
                      onClick={onDelete}
                      disabled={deleting}
                    >
                      {deleting ? <Loader2 className="size-4 animate-spin" /> : "Eliminar"}
                    </Button>
                  </div>
                </div>
              )}
            </div>
          )}
        </DialogPrimitive.Content>
      </DialogPrimitive.Portal>
    </DialogPrimitive.Root>
  );
}
