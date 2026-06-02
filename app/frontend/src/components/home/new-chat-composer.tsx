import { ArrowUp } from "lucide-react";
import { useAutoGrowTextarea } from "@/hooks/chat/useAutoGrowTextarea";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { CourseResponse } from "@/types/course";

const MAX_CHARS = 1500;

interface NewChatComposerProps {
  courses: CourseResponse[];
  selectedCourse: string;
  onCourseChange: (code: string) => void;
  input: string;
  onInputChange: (value: string) => void;
  onSubmit: () => void;
  submitting: boolean;
}

export function NewChatComposer({
  courses,
  selectedCourse,
  onCourseChange,
  input,
  onInputChange,
  onSubmit,
  submitting,
}: NewChatComposerProps) {
  const textareaRef = useAutoGrowTextarea(input, 160);
  
  const canSubmit = !submitting && !!input.trim() && !!selectedCourse;
  const nearLimit = input.length >= MAX_CHARS * 0.9;

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit();
  };

  return (
    <form onSubmit={handleFormSubmit} className="w-full">
      <div className="flex items-end gap-2 rounded-[1.75rem] border border-border/70 bg-card/80 py-2 pl-4 pr-2 shadow-lg backdrop-blur-sm transition-colors focus-within:border-primary/40 focus-within:ring-2 focus-within:ring-primary/20">
        <textarea
          ref={textareaRef}
          value={input}
          maxLength={MAX_CHARS}
          onChange={(e) => onInputChange(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              onSubmit();
            }
          }}
          placeholder="Pergunte alguma coisa"
          rows={1}
          className="max-h-[160px] min-h-[2.25rem] min-w-0 flex-1 resize-none self-center bg-transparent py-1.5 text-sm leading-relaxed outline-none placeholder:text-muted-foreground"
          disabled={submitting}
        />

        <div className="flex shrink-0 items-center gap-2">
          {nearLimit && (
            <span className="text-[11px] tabular-nums text-muted-foreground/70">
              {input.length}/{MAX_CHARS}
            </span>
          )}

          <Select
            value={selectedCourse}
            onValueChange={onCourseChange}
            disabled={submitting || courses.length === 0}
          >
            <SelectTrigger
              size="sm"
              className="h-9 max-w-[12rem] rounded-full border-0 bg-muted/60 text-xs font-medium shadow-none hover:bg-muted focus-visible:ring-0"
            >
              <SelectValue
                placeholder={
                  courses.length === 0 ? "Sem cadeiras" : "Selecione a cadeira"
                }
              />
            </SelectTrigger>
            <SelectContent position="popper" side="top" align="end">
              {courses.map((course) => (
                <SelectItem key={course.code} value={course.code}>
                  {course.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <button
            type="submit"
            disabled={!canSubmit}
            aria-label="Iniciar conversa"
            title="Iniciar conversa"
            className="flex size-9 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground transition-all hover:bg-primary/90 hover:scale-105 active:scale-95 disabled:pointer-events-none disabled:opacity-40 disabled:hover:scale-100"
          >
            <ArrowUp className="size-5" />
          </button>
        </div>
      </div>
    </form>
  );
}