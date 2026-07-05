import { forwardRef, type MutableRefObject, type ReactNode } from "react";
import { Label } from "@/components/ui/label";
import { useAutoGrowTextarea } from "@/hooks/chat/useAutoGrowTextarea";
import { cn } from "@/lib/utils";

interface FormTextareaProps extends React.ComponentProps<"textarea"> {
  id: string;
  label: ReactNode;
  error?: string;
  headerEnd?: ReactNode;
  autoGrowValue?: string;
  maxAutoGrowHeight?: number;
}

export const FormTextarea = forwardRef<HTMLTextAreaElement, FormTextareaProps>(
  (
    {
      id,
      label,
      error,
      headerEnd,
      autoGrowValue = "",
      maxAutoGrowHeight = 220,
      className,
      ...props
    },
    ref
  ) => {
    const textareaRef = useAutoGrowTextarea(autoGrowValue, maxAutoGrowHeight);

    return (
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <Label htmlFor={id}>{label}</Label>
          {headerEnd}
        </div>
        <textarea
          id={id}
          aria-invalid={!!error}
          rows={3}
          ref={(el) => {
            textareaRef.current = el;
            if (typeof ref === "function") ref(el);
            else if (ref) (ref as MutableRefObject<HTMLTextAreaElement | null>).current = el;
          }}
          className={cn(
            "min-h-24 w-full min-w-0 resize-none overflow-y-auto rounded-xl border border-input bg-transparent px-4 py-3 text-[15px] leading-relaxed transition-colors outline-none placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 disabled:pointer-events-none disabled:cursor-not-allowed disabled:bg-input/50 disabled:opacity-50 aria-invalid:border-destructive aria-invalid:ring-3 aria-invalid:ring-destructive/20 dark:bg-input/30 dark:disabled:bg-input/80 dark:aria-invalid:border-destructive/50 dark:aria-invalid:ring-destructive/40",
            className
          )}
          {...props}
        />
        {error && <p className="text-xs text-destructive">{error}</p>}
      </div>
    );
  }
);

FormTextarea.displayName = "FormTextarea";
