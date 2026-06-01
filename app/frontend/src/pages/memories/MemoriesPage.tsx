import { useState } from "react";
import { ArrowLeft, Brain } from "lucide-react";
import { useNavigate } from "react-router";

import { Button } from "@/components/ui/button";
import { PageState } from "@/components/ui/page-state";
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
import type { UserMemory } from "@/api/memory";

export default function MemoriesPage() {
  const navigate = useNavigate();
  const {
    courses,
    selectedCourse,
    setSelectedCourse,
    memories,
    loading,
    loadingMemories,
    error,
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
    <PageState loading={loading} error={error} onRetry={() => window.location.reload()}>
      <main className="mx-auto w-full max-w-2xl px-6 py-10">
        <Button
          variant="ghost"
          size="sm"
          className="mb-6 -ml-2 text-muted-foreground"
          onClick={() => navigate("/")}
        >
          <ArrowLeft className="size-4" />
          Voltar
        </Button>

        <div className="mb-6 flex items-start gap-3">
          <div className="flex size-10 shrink-0 items-center justify-center rounded-full bg-primary/10">
            <Brain className="size-5 text-primary" />
          </div>
          <div className="space-y-1">
            <h1 className="text-2xl font-semibold tracking-tight">Memorias guardadas</h1>
            <p className="text-sm text-muted-foreground">
              Informações que o tutor guardou sobre si para personalizar as respostas.
              Pode remover as que nao queira manter.
            </p>
          </div>
        </div>

        {courses.length === 0 ? (
          <div className="rounded-lg border border-dashed py-12 text-center text-sm text-muted-foreground">
            Não tem cadeiras associadas.
          </div>
        ) : (
          <>
            <div className="mb-4">
              <Select value={selectedCourse} onValueChange={setSelectedCourse}>
                <SelectTrigger className="min-w-56">
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

            <MemoryList
              memories={memories}
              loading={loadingMemories}
              deletingId={deletingId}
              onRequestDelete={setPendingDelete}
            />
          </>
        )}
      </main>

      <DeleteMemoryDialog
        memory={pendingDelete}
        deleting={deletingId !== null}
        onConfirm={handleConfirmDelete}
        onOpenChange={(open) => !open && setPendingDelete(null)}
      />
    </PageState>
  );
}
