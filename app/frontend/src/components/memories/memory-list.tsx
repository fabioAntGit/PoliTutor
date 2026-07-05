import { Loader2, Trash2 } from "lucide-react";

import { formatRelativeDate } from "@/lib/date";
import type { MemoryType, UserMemory } from "@/types/memory";

const TYPE_LABELS: Record<MemoryType, string> = {
  difficulty: "Dificuldade",
  preference: "Preferência",
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
      <div className="flex items-center justify-center rounded-2xl border bg-card/40 py-16">
        <Loader2 className="size-5 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (memories.length === 0) {
    return (
      <div className="rounded-2xl border border-dashed bg-card/20 px-6 py-16 text-center text-sm text-muted-foreground">
        O tutor ainda não guardou memórias sobre si nesta cadeira.
      </div>
    );
  }

  return (
    <ul className="divide-y divide-border/60 overflow-hidden rounded-2xl border bg-card/40">
      {memories.map((memory) => (
        <li
          key={memory.id}
          className="group flex items-start gap-4 px-5 py-4 transition-colors hover:bg-muted/30"
        >
          <div className="min-w-0 flex-1 space-y-1.5">
            <span className="-ml-2 inline-block rounded-full bg-muted px-2 py-0.5 text-[11px] font-medium text-muted-foreground">
              {TYPE_LABELS[memory.type]}
            </span>
            <p className="text-sm leading-relaxed text-foreground">
              {memory.content}
            </p>
            <p className="text-xs text-muted-foreground/60">
              Atualizada {formatRelativeDate(memory.last_seen_at)}
            </p>
          </div>

          <button
            type="button"
            disabled={deletingId === memory.id}
            onClick={() => onRequestDelete(memory)}
            aria-label="Remover memória"
            title="Remover memória"
            className="flex size-8 shrink-0 items-center justify-center rounded-lg text-muted-foreground/60 transition-colors hover:bg-destructive/10 hover:text-destructive focus-visible:opacity-100 disabled:pointer-events-none sm:opacity-0 sm:group-hover:opacity-100"
          >
            {deletingId === memory.id ? (
              <Loader2 className="size-4 animate-spin" />
            ) : (
              <Trash2 className="size-4" />
            )}
          </button>
        </li>
      ))}
    </ul>
  );
}
