import { useState } from "react";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { MemoryList } from "@/components/memories/memory-list";
import { DeleteMemoryDialog } from "@/components/memories/delete-memory-dialog";
import { useMemories } from "@/hooks/memories/useMemories";
import type { UserMemory } from "@/types/memory";

export function MemoriesSection() {
  const {
    courses,
    selectedCourse,
    setSelectedCourse,
    memories,
    loadingMemories,
    deletingId,
    deleteMemory,
  } = useMemories();

  const [pendingDelete, setPendingDelete] = useState<UserMemory | null>(null);

  const handleConfirmDelete = async () => {
    if (!pendingDelete) return;
    await deleteMemory(pendingDelete.id);
    setPendingDelete(null);
  };

  return (
    <div className="space-y-5">
      <p className="max-w-prose text-[13px] leading-relaxed text-muted-foreground">
        Informações que o tutor guardou sobre si para personalizar as respostas.
        Pode remover as que não queira manter.
      </p>

      {courses.length === 0 ? (
        <div className="rounded-2xl border border-dashed bg-card/20 px-6 py-16 text-center text-sm text-muted-foreground">
          Não tem cadeiras associadas.
        </div>
      ) : (
        <div className="space-y-3">
          <div className="flex items-center justify-between gap-3 border-b pb-3">
            <div className="flex items-center gap-2">
              <Select value={selectedCourse} onValueChange={setSelectedCourse}>
                <SelectTrigger size="sm" className="text-sm">
                  <SelectValue placeholder="Selecione uma cadeira" />
                </SelectTrigger>
                <SelectContent position="popper" side="bottom" align="start">
                  {courses.map((course) => (
                    <SelectItem key={course.code} value={course.code}>
                      {course.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {!loadingMemories && memories.length > 0 && (
              <span className="shrink-0 text-xs tabular-nums text-muted-foreground">
                {memories.length} {memories.length === 1 ? "memória" : "memórias"}
              </span>
            )}
          </div>

          <MemoryList
            memories={memories}
            loading={loadingMemories}
            deletingId={deletingId}
            onRequestDelete={setPendingDelete}
          />
        </div>
      )}

      <DeleteMemoryDialog
        memory={pendingDelete}
        deleting={deletingId !== null}
        onConfirm={handleConfirmDelete}
        onOpenChange={(open) => !open && setPendingDelete(null)}
      />
    </div>
  );
}
