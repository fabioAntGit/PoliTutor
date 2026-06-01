import { Loader2, Trash2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatRelativeDate } from "@/lib/date";
import type { MemoryType, UserMemory } from "@/api/memory";

const TYPE_LABELS: Record<MemoryType, string> = {
  difficulty: "Dificuldade",
  preference: "Preferencia",
  goal: "Objetivo",
  progress: "Progresso",
};

interface MemoryListProps {
  memories: UserMemory[];
  loading: boolean;
  deletingId: string | null;
  onRequestDelete: (memory: UserMemory) => void;
}

export function MemoryList({
  memories,
  loading,
  deletingId,
  onRequestDelete,
}: MemoryListProps) {
  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="size-6 animate-spin text-primary" />
      </div>
    );
  }

  if (memories.length === 0) {
    return (
      <div className="rounded-lg border border-dashed py-12 text-center text-sm text-muted-foreground">
        O tutor ainda não guardou memórias sobre si nesta cadeira.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {memories.map((memory) => (
        <Card key={memory.id}>
          <CardHeader className="flex flex-row items-start justify-between gap-3 space-y-0">
            <div className="space-y-1">
              <span className="inline-block rounded-full bg-muted px-2 py-0.5 text-[11px] font-medium text-muted-foreground">
                {TYPE_LABELS[memory.type]}
              </span>
              <CardTitle className="text-base">{memory.topic}</CardTitle>
            </div>
            <Button
              type="button"
              variant="ghost"
              size="icon-sm"
              title="Remover memória"
              aria-label="Remover memória"
              disabled={deletingId === memory.id}
              onClick={() => onRequestDelete(memory)}
            >
              {deletingId === memory.id ? (
                <Loader2 className="size-4 animate-spin" />
              ) : (
                <Trash2 className="size-4 text-destructive" />
              )}
            </Button>
          </CardHeader>
          <CardContent className="space-y-2">
            <p className="text-sm text-muted-foreground">{memory.content}</p>
            <p className="text-xs text-muted-foreground/70">
              Atualizada {formatRelativeDate(memory.last_seen_at)}
            </p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
