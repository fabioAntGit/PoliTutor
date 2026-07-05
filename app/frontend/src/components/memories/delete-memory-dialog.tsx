import { Dialog as DialogPrimitive } from "radix-ui";
import { AlertTriangle, Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import type { UserMemory } from "@/types/memory";

interface DeleteMemoryDialogProps {
  memory: UserMemory | null;
  deleting: boolean;
  onConfirm: () => void;
  onOpenChange: (open: boolean) => void;
}

export function DeleteMemoryDialog({
  memory,
  deleting,
  onConfirm,
  onOpenChange,
}: DeleteMemoryDialogProps) {
  const handleClose = () => {
    if (deleting) return;
    onOpenChange(false);
  };

  return (
    <DialogPrimitive.Root open={memory !== null} onOpenChange={(o) => !o && handleClose()}>
      <DialogPrimitive.Portal>
        <DialogPrimitive.Overlay className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm" />
        <DialogPrimitive.Content className="fixed left-1/2 top-1/2 z-50 w-full max-w-md -translate-x-1/2 -translate-y-1/2 rounded-lg border bg-background p-6 shadow-lg">
          <div className="flex items-start gap-3">
            <div className="flex size-10 shrink-0 items-center justify-center rounded-full bg-destructive/10">
              <AlertTriangle className="size-5 text-destructive" />
            </div>
            <div className="flex-1 space-y-1">
              <DialogPrimitive.Title className="text-lg font-semibold">
                Remover memória
              </DialogPrimitive.Title>
              <DialogPrimitive.Description className="text-sm text-muted-foreground">
                O tutor deixará de ter em conta esta informação sobre si. Esta ação não
                pode ser anulada.
              </DialogPrimitive.Description>
            </div>
          </div>

          {memory && (
            <div className="mt-4 rounded-md border bg-muted/40 p-3 text-sm text-muted-foreground">
              {memory.content}
            </div>
          )}

          <div className="mt-6 flex gap-2">
            <Button
              type="button"
              variant="outline"
              className="flex-1"
              onClick={handleClose}
              disabled={deleting}
            >
              Cancelar
            </Button>
            <Button
              type="button"
              variant="destructive"
              className="flex-1"
              onClick={onConfirm}
              disabled={deleting}
            >
              {deleting ? <Loader2 className="size-4 animate-spin" /> : "Remover"}
            </Button>
          </div>
        </DialogPrimitive.Content>
      </DialogPrimitive.Portal>
    </DialogPrimitive.Root>
  );
}
