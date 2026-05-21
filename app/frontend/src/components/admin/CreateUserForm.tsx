import { Controller } from "react-hook-form";
import { Loader2, X, Sparkles } from "lucide-react";
import { generatePassword } from "@/lib/password";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { PasswordInput } from "@/components/password-input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useCreateUser } from "@/hooks/admin/useCreateUser";
import CreatedUserDialog from "@/components/admin/CreatedUserDialog";

export default function CreateUserForm() {
  const { form, courses, createdUser, dismissCreatedUser, onSubmit } = useCreateUser();
  const {
    register,
    control,
    formState: { errors, isSubmitting },
  } = form;

  return (
    <>
      <form onSubmit={onSubmit} className="space-y-5">
        <div className="space-y-2">
          <Label htmlFor="full_name">Nome completo</Label>
          <Input
            id="full_name"
            placeholder="João Silva"
            aria-invalid={!!errors.full_name}
            {...register("full_name")}
          />
          {errors.full_name && (
            <p className="text-xs text-destructive">{errors.full_name.message}</p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="email">Email</Label>
          <Input
            id="email"
            type="email"
            placeholder="joao.silva@estg.ipp.pt"
            aria-invalid={!!errors.email}
            {...register("email")}
          />
          {errors.email && (
            <p className="text-xs text-destructive">{errors.email.message}</p>
          )}
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <Label htmlFor="password">Password</Label>
            <button
              type="button"
              onClick={() =>
                form.setValue("password", generatePassword(11), {
                  shouldValidate: true,
                  shouldDirty: true,
                })
              }
              className="inline-flex items-center gap-1 text-xs text-primary hover:underline"
            >
              <Sparkles className="size-3" />
              Gerar password
            </button>
          </div>
          <PasswordInput
            id="password"
            aria-invalid={!!errors.password}
            {...register("password")}
          />
          {errors.password && (
            <p className="text-xs text-destructive">{errors.password.message}</p>
          )}
        </div>

        <div className="space-y-2">
          <Label>Role</Label>
          <Controller
            name="role"
            control={control}
            render={({ field }) => (
              <Select value={field.value} onValueChange={field.onChange}>
                <SelectTrigger aria-invalid={!!errors.role} className="w-full">
                  <SelectValue placeholder="Seleciona um role" />
                </SelectTrigger>
                <SelectContent position="popper" align="start">
                  <SelectItem value="student">Estudante</SelectItem>
                  <SelectItem value="teacher">Professor</SelectItem>
                </SelectContent>
              </Select>
            )}
          />
          {errors.role && (
            <p className="text-xs text-destructive">{errors.role.message}</p>
          )}
        </div>

        {courses.length > 0 && (
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
        )}

        {errors.root && (
          <p className="text-sm text-destructive p-2 bg-destructive/10 rounded-md text-center">
            {errors.root.message}
          </p>
        )}

        <Button
          type="submit"
          size="lg"
          className="w-full h-12 text-base font-semibold"
          disabled={isSubmitting}
        >
          {isSubmitting ? <Loader2 className="size-4 animate-spin" /> : "Criar utilizador"}
        </Button>
      </form>

      <CreatedUserDialog user={createdUser} onClose={dismissCreatedUser} />
    </>
  );
}
