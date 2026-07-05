import { CheckCircle } from "lucide-react";
import { FormField } from "@/components/form/form-field";
import { FormRootError } from "@/components/form/form-root-error";
import { FormTextarea } from "@/components/form/form-textarea";
import { SubmitButton } from "@/components/form/submit-button";
import { useCreateCourse } from "@/hooks/admin/useCreateCourse";
import { COURSE_CODE_MAX_LENGTH, COURSE_NAME_MAX_LENGTH, COURSE_SCOPE_MAX_LENGTH } from "@/lib/validation";

export default function CreateCourseForm() {
  const { form, success, onSubmit } = useCreateCourse();
  const {
    register,
    formState: { errors, isSubmitting },
  } = form;
  const scopeValue = form.watch("scope");

  return (
    <form onSubmit={onSubmit} className="space-y-5">
      <FormField
        id="code"
        label="Código"
        placeholder="ex: ed"
        maxLength={COURSE_CODE_MAX_LENGTH}
        error={errors.code?.message}
        {...register("code")}
      />

      <FormField
        id="name"
        label="Nome"
        placeholder="ex: Estruturas de Dados"
        maxLength={COURSE_NAME_MAX_LENGTH}
        error={errors.name?.message}
        {...register("name")}
      />

      <FormTextarea
        id="scope"
        label="Âmbito"
        placeholder="Ex: Listas, pilhas, filas, árvores e grafos."
        autoGrowValue={scopeValue}
        maxLength={COURSE_SCOPE_MAX_LENGTH}
        error={errors.scope?.message}
        {...register("scope")}
      />

      <FormRootError message={errors.root?.message} />

      {success && (
        <div className="flex items-center gap-2 text-sm text-green-600 p-2 bg-green-50 rounded-md">
          <CheckCircle className="size-4" />
          Cadeira criada com sucesso.
        </div>
      )}

      <SubmitButton loading={isSubmitting}>Criar cadeira</SubmitButton>
    </form>
  );
}
