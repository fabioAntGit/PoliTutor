import { Controller } from "react-hook-form";
import { X, Sparkles } from "lucide-react";
import { generatePassword } from "@/lib/password";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { FormField } from "@/components/form/form-field";
import { FormPasswordField } from "@/components/form/form-password-field";
import { FormRootError } from "@/components/form/form-root-error";
import { SubmitButton } from "@/components/form/submit-button";
import { useCreateUser } from "@/hooks/admin/useCreateUser";
import CreatedUserDialog from "@/components/admin/created-user-dialog";

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
        <FormField
          id="full_name"
          label="Nome completo"
          placeholder="João Silva"
          error={errors.full_name?.message}
          {...register("full_name")}
        />

        <FormField
          id="email"
          label="Email"
          type="email"
          placeholder="joao.silva@ipp.pt"
          error={errors.email?.message}
          {...register("email")}
        />

        <FormPasswordField
          id="password"
          label="Password"
          error={errors.password?.message}
          headerEnd={
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
          }
          {...register("password")}
        />

        <div className="space-y-2">
          <Label>Cargo</Label>
          <Controller
            name="role"
            control={control}
            render={({ field }) => (
              <Select value={field.value} onValueChange={field.onChange}>
                <SelectTrigger aria-invalid={!!errors.role} className="w-full">
                  <SelectValue placeholder="Seleciona um cargo" />
                </SelectTrigger>
                <SelectContent position="popper" align="start">
                  <SelectItem value="student">Aluno</SelectItem>
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
                const available = courses.filter((c) => !field.value.includes(c.id));
                const selected = courses.filter((c) => field.value.includes(c.id));
                return (
                  <div className="space-y-2">
                    <Select
                      key={field.value.length}
                      onValueChange={(id) => {
                        if (id && !field.value.includes(id)) {
                          field.onChange([...field.value, id]);
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
                            <SelectItem key={course.id} value={course.id}>
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
                            key={course.id}
                            className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium bg-primary/10 text-primary rounded-full"
                          >
                            <span className="font-mono uppercase">{course.code}</span>
                            <span className="opacity-70">·</span>
                            {course.name}
                            <button
                              type="button"
                              onClick={() =>
                                field.onChange(field.value.filter((c) => c !== course.id))
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

        <FormRootError message={errors.root?.message} />

        <SubmitButton loading={isSubmitting}>Criar utilizador</SubmitButton>
      </form>

      <CreatedUserDialog user={createdUser} onClose={dismissCreatedUser} />
    </>
  );
}
