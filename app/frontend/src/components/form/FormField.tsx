import { forwardRef, type ReactNode } from "react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

interface FormFieldProps extends React.ComponentProps<"input"> {
  id: string;
  label: ReactNode;
  error?: string;
  headerEnd?: ReactNode;
}

export const FormField = forwardRef<HTMLInputElement, FormFieldProps>(
  ({ id, label, error, headerEnd, ...props }, ref) => {
    return (
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <Label htmlFor={id}>{label}</Label>
          {headerEnd}
        </div>
        <Input id={id} aria-invalid={!!error} ref={ref} {...props} />
        {error && <p className="text-xs text-destructive">{error}</p>}
      </div>
    );
  }
);

FormField.displayName = "FormField";
