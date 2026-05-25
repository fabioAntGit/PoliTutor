import { ArrowUp } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { CourseResponse } from "@/types/course";

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
  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit();
  };

  const canSubmit = !submitting && !!input.trim() && !!selectedCourse;

  return (
    <form onSubmit={handleFormSubmit} className="space-y-3">
      <div className="rounded-xl border bg-card shadow-sm">
        <textarea
          value={input}
          onChange={(e) => onInputChange(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              onSubmit();
            }
          }}
          placeholder="Escreve a tua mensagem..."
          rows={5}
          maxLength={1500}
          className="w-full resize-none rounded-t-xl bg-transparent px-4 py-3 text-sm outline-none"
          disabled={submitting}
        />

        <div className="flex items-center justify-between gap-2 border-t px-3 py-2">
          <Select
            value={selectedCourse}
            onValueChange={onCourseChange}
            disabled={submitting || courses.length === 0}
          >
            <SelectTrigger size="sm" className="min-w-48">
              <SelectValue
                placeholder={
                  courses.length === 0
                    ? "Sem cadeiras disponiveis"
                    : "Seleciona uma cadeira"
                }
              />
            </SelectTrigger>
            <SelectContent position="popper" side="bottom" align="start">
              {courses.map((course) => (
                <SelectItem key={course.code} value={course.code}>
                  {course.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Button
            type="submit"
            size="icon-sm"
            disabled={!canSubmit}
            title="Iniciar conversa"
          >
            <ArrowUp className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </form>
  );
}
