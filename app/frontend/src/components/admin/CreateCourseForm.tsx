import { CheckCircle, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useCreateCourse } from "@/hooks/admin/useCreateCourse";

export default function CreateCourseForm() {
  const { form, success, onSubmit } = useCreateCourse();
  const {
    register,
    formState: { errors, isSubmitting },
  } = form;

  return (
    <form onSubmit={onSubmit} className="space-y-5">
      <div className="space-y-2">
        <Label htmlFor="code">Código</Label>
        <Input
          id="code"
          placeholder="ex: ed"
          aria-invalid={!!errors.code}
          {...register("code")}
        />
        {errors.code && <p className="text-xs text-destructive">{errors.code.message}</p>}
      </div>

      <div className="space-y-2">
        <Label htmlFor="name">Nome</Label>
        <Input
          id="name"
          placeholder="ex: Estruturas de Dados"
          aria-invalid={!!errors.name}
          {...register("name")}
        />
        {errors.name && <p className="text-xs text-destructive">{errors.name.message}</p>}
      </div>

      <div className="space-y-2">
        <Label htmlFor="description">Descrição (opcional)</Label>
        <Input
          id="description"
          placeholder="Breve descrição da cadeira"
          {...register("description")}
        />
      </div>

      {errors.root && (
        <p className="text-sm text-destructive p-2 bg-destructive/10 rounded-md text-center">
          {errors.root.message}
        </p>
      )}

      {success && (
        <div className="flex items-center gap-2 text-sm text-green-600 p-2 bg-green-50 rounded-md">
          <CheckCircle className="size-4" />
          Cadeira criada com sucesso.
        </div>
      )}

      <Button
        type="submit"
        size="lg"
        className="w-full h-12 text-base font-semibold"
        disabled={isSubmitting}
      >
        {isSubmitting ? <Loader2 className="size-4 animate-spin" /> : "Criar cadeira"}
      </Button>
    </form>
  );
}
