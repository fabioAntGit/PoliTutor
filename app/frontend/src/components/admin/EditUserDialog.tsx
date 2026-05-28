import { useState, useEffect } from "react";
import { Controller } from "react-hook-form";
import { Dialog as DialogPrimitive } from "radix-ui";
import { Loader2, X, Trash2, AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useEditUser } from "@/hooks/admin/useEditUser";
import type { UserResponse } from "@/types/user";
import type { CourseResponse } from "@/types/course";

interface EditUserDialogProps {
  user: UserResponse | null;
  courses: CourseResponse[];
  onClose: () => void;
  onSaved: () => void;
}

export default function EditUserDialog({ user, courses, onClose, onSaved }: EditUserDialogProps) {
  const { form, onSubmit, onDelete, deleting, deleteError } = useEditUser(user, onSaved);
  const [confirmDelete, setConfirmDelete] = useState(false);

  const {
    register,
    control,
    formState: { errors, isSubmitting },
  } = form;

  useEffect(() => {
    if (!user) setConfirmDelete(false);
  }, [user]);

  return (
    <DialogPrimitive.Root open={!!user} onOpenChange={(open) => !open && onClose()}>
      <DialogPrimitive.Portal>
        <DialogPrimitive.Overlay className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm" />
        <DialogPrimitive.Content className="fixed left-1/2 top-1/2 z-50 w-full max-w-md -translate-x-1/2 -translate-y-1/2 rounded-lg border bg-background p-6 shadow-lg max-h-[90vh] overflow-y-auto">
          <DialogPrimitive.Title className="text-lg font-semibold">
            Editar utilizador
          </DialogPrimitive.Title>
          <DialogPrimitive.Description className="text-sm text-muted-foreground mb-4">
            @{user?.username}
          </DialogPrimitive.Description>

          <form onSubmit={onSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="edit-full_name">Nome completo</Label>
              <Input
                id="edit-full_name"
                aria-invalid={!!errors.full_name}
                {...register("full_name")}
              />
              {errors.full_name && (
                <p className="text-xs text-destructive">{errors.full_name.message}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="edit-email">Email</Label>
              <Input
                id="edit-email"
                type="email"
                aria-invalid={!!errors.email}
                {...register("email")}
              />
              {errors.email && (
                <p className="text-xs text-destructive">{errors.email.message}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label>Role</Label>
              <Controller
                name="role"
                control={control}
                render={({ field }) => (
                  <Select value={field.value} onValueChange={field.onChange}>
                    <SelectTrigger className="w-full" aria-invalid={!!errors.role}>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent position="popper" align="start">
                      <SelectItem value="student">Estudante</SelectItem>
                      <SelectItem value="teacher">Professor</SelectItem>
                      <SelectItem value="admin">Admin</SelectItem>
                    </SelectContent>
                  </Select>
                )}
              />
            </div>

            <div className="space-y-2">
              <Label>Cadeiras</Label>
              <Controller
                name="courses"
                control={control}
                render={({ field }) => {
                  const available = courses.filter((c) => !field.value.includes(c.code));
                  const selected = courses.filter((c) => field.value.includes(c.code));
                  return (
                    <div className="space-y-2">
                      <Select
                        key={field.value.length}
                        onValueChange={(code) => {
                          if (code && !field.value.includes(code)) {
                            field.onChange([...field.value, code]);
                          }
                        }}
                      >
                        <SelectTrigger className="w-full">
                          <SelectValue placeholder="Adicionar cadeira" />
                        </SelectTrigger>
                        <SelectContent position="popper" align="start" className="max-h-60">
                          {available.length === 0 ? (
                            <div className="px-2 py-1.5 text-sm text-muted-foreground">
                              Sem cadeiras disponíveis
                            </div>
                          ) : (
                            available.map((course) => (
                              <SelectItem key={course.code} value={course.code}>
                                <span className="font-mono text-xs uppercase mr-1">
                                  {course.code}
                                </span>
                                {course.name}
                              </SelectItem>
                            ))
                          )}
                        </SelectContent>
                      </Select>

                      {selected.length > 0 && (
                        <div className="flex flex-wrap gap-2 max-h-32 overflow-y-auto p-1 border rounded-md">
                          {selected.map((course) => (
                            <span
                              key={course.code}
                              className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium bg-primary/10 text-primary rounded-full"
                            >
                              <span className="font-mono uppercase">{course.code}</span>
                              <span className="opacity-70">·</span>
                              {course.name}
                              <button
                                type="button"
                                onClick={() =>
                                  field.onChange(field.value.filter((c) => c !== course.code))
                                }
                                className="hover:bg-primary/20 rounded-full p-0.5 transition-colors"
                                aria-label={`Remover ${course.name}`}
                              >
                                <X className="size-3" />
                              </button>
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  );
                }}
              />
            </div>

            {errors.root && (
              <p className="text-sm text-destructive p-2 bg-destructive/10 rounded-md text-center">
                {errors.root.message}
              </p>
            )}

            <div className="flex gap-2 pt-2">
              <Button type="button" variant="outline" className="flex-1" onClick={onClose}>
                Cancelar
              </Button>
              <Button type="submit" className="flex-1" disabled={isSubmitting}>
                {isSubmitting ? <Loader2 className="size-4 animate-spin" /> : "Guardar"}
              </Button>
            </div>
          </form>

          {user?.is_active && (
            <div className="mt-6 pt-4 border-t">
              {!confirmDelete ? (
                <Button
                  type="button"
                  variant="ghost"
                  className="w-full text-destructive hover:bg-destructive/10 hover:text-destructive"
                  onClick={() => setConfirmDelete(true)}
                >
                  <Trash2 className="size-4 mr-2" />
                  Eliminar utilizador
                </Button>
              ) : (
                <div className="space-y-3 p-3 bg-destructive/5 border border-destructive/20 rounded-md">
                  <div className="flex items-start gap-2">
                    <AlertTriangle className="size-4 text-destructive flex-shrink-0 mt-0.5" />
                    <p className="text-sm">
                      Tens a certeza? O utilizador <strong>@{user.username}</strong> deixa de poder
                      aceder à plataforma.
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
