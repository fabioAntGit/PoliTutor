import { CheckCircle } from "lucide-react";
import { FormField } from "@/components/form/form-field";
import { FormRootError } from "@/components/form/form-root-error";
import { SubmitButton } from "@/components/form/submit-button";
import { useCreateCourse } from "@/hooks/admin/useCreateCourse";

export default function CreateCourseForm() {
  const { form, success, onSubmit } = useCreateCourse();
  const {
    register,
    formState: { errors, isSubmitting },
  } = form;

  return (
    <form onSubmit={onSubmit} className="space-y-5">
      <FormField
        id="code"
        label="Código"
        placeholder="ex: ed"
        error={errors.code?.message}
        {...register("code")}
      />

      <FormField
        id="name"
        label="Nome"
        placeholder="ex: Estruturas de Dados"
        error={errors.name?.message}
        {...register("name")}
      />

      <FormField
        id="scope"
        label="Âmbito"
        placeholder="Ex: Listas, pilhas, filas, árvores e grafos."
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
