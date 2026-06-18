import { useState } from "react";
import { Dialog as DialogPrimitive } from "radix-ui";
import { AlertTriangle, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { useNavigate } from "react-router";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { UserService } from "@/services/user.service";
import { AuthService } from "@/services/auth.service";
import { ApiError } from "@/lib/errors";

interface DeleteAccountDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const CONFIRM_PHRASE = "ELIMINAR";

export function DeleteAccountDialog({ open, onOpenChange }: DeleteAccountDialogProps) {
  const navigate = useNavigate();
  const [confirmation, setConfirmation] = useState("");
  const [deleting, setDeleting] = useState(false);

  const canDelete = confirmation === CONFIRM_PHRASE && !deleting;

  const handleClose = () => {
    if (deleting) return;
    setConfirmation("");
    onOpenChange(false);
  };

  const handleDelete = async () => {
    if (!canDelete) return;
    setDeleting(true);
    try {
      await UserService.deleteMyAccount();
      AuthService.clearTokens();
      toast.success("Conta eliminada. Os teus dados serao apagados permanentemente daqui a 30 dias.");
      navigate("/login", { replace: true });
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Erro ao eliminar conta.";
      toast.error(message);
      setDeleting(false);
    }
  };

  return (
    <DialogPrimitive.Root open={open} onOpenChange={(o) => !o && handleClose()}>
      <DialogPrimitive.Portal>
        <DialogPrimitive.Overlay className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm" />
        <DialogPrimitive.Content className="fixed left-1/2 top-1/2 z-50 w-full max-w-md -translate-x-1/2 -translate-y-1/2 rounded-lg border bg-background p-6 shadow-lg">
          <div className="flex items-start gap-3">
            <div className="flex size-10 shrink-0 items-center justify-center rounded-full bg-destructive/10">
              <AlertTriangle className="size-5 text-destructive" />
            </div>
            <div className="flex-1 space-y-1">
              <DialogPrimitive.Title className="text-lg font-semibold">
                Eliminar conta
              </DialogPrimitive.Title>
              <DialogPrimitive.Description className="text-sm text-muted-foreground">
                Esta ação remove a sua conta, conversas e memórias do tutor. Os dados ficam
                retidos durante 30 dias e depois são apagados de forma permanente.
              </DialogPrimitive.Description>
            </div>
          </div>

          <div className="mt-4 space-y-2">
            <Label htmlFor="delete-confirm">
              Para confirmar, escreva <span className="font-mono font-semibold">{CONFIRM_PHRASE}</span>
            </Label>
            <Input
              id="delete-confirm"
              value={confirmation}
              onChange={(e) => setConfirmation(e.target.value)}
              autoComplete="off"
              disabled={deleting}
            />
          </div>

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
              onClick={handleDelete}
              disabled={!canDelete}
            >
              {deleting ? <Loader2 className="size-4 animate-spin" /> : "Eliminar conta"}
            </Button>
          </div>
        </DialogPrimitive.Content>
      </DialogPrimitive.Portal>
    </DialogPrimitive.Root>
  );
}
