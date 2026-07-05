import { forwardRef, type ReactNode } from "react";
import { Label } from "@/components/ui/label";
import { PasswordInput } from "@/components/password-input";

interface FormPasswordFieldProps extends React.ComponentProps<"input"> {
  id: string;
  label: ReactNode;
  error?: string;
  headerEnd?: ReactNode;
}

export const FormPasswordField = forwardRef<HTMLInputElement, FormPasswordFieldProps>(
  ({ id, label, error, headerEnd, ...props }, ref) => {
    return (
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <Label htmlFor={id}>{label}</Label>
          {headerEnd}
        </div>
        <PasswordInput id={id} aria-invalid={!!error} ref={ref} {...props} />
        {error && <p className="text-xs text-destructive">{error}</p>}
      </div>
    );
  }
);

FormPasswordField.displayName = "FormPasswordField";
