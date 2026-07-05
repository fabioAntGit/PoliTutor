import { useState } from "react";
import { Dialog as DialogPrimitive } from "radix-ui";
import { AlertTriangle, Eye, EyeOff, Copy } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import type { CreatedUserCredentials } from "@/types/user";

interface CreatedUserDialogProps {
  user: CreatedUserCredentials | null;
  onClose: () => void;
}

export default function CreatedUserDialog({ user, onClose }: CreatedUserDialogProps) {
  const [showPassword, setShowPassword] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleClose = () => {
    setShowPassword(false);
    onClose();
  };

  const copyCredentials = async () => {
    if (!user) return;
    await navigator.clipboard.writeText(
      `Username: ${user.username}\nPalavra-passe: ${user.password}`,
    );
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <DialogPrimitive.Root open={!!user} onOpenChange={(open) => !open && handleClose()}>
      <DialogPrimitive.Portal>
        <DialogPrimitive.Overlay className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm" />
        <DialogPrimitive.Content className="fixed left-1/2 top-1/2 z-50 w-full max-w-md -translate-x-1/2 -translate-y-1/2 rounded-lg border bg-background p-6 shadow-lg">
          <div className="space-y-4">
            <div className="flex items-start gap-3">
              <div className="flex-shrink-0 p-2 bg-amber-100 text-amber-700 rounded-full">
                <AlertTriangle className="size-5" />
              </div>
              <div className="space-y-1">
                <DialogPrimitive.Title className="text-lg font-semibold">
                  Utilizador criado com sucesso
                </DialogPrimitive.Title>
                <DialogPrimitive.Description className="text-sm text-muted-foreground">
                  Comunica estas credenciais ao utilizador. Esta palavra-passe não será mostrada novamente.
                </DialogPrimitive.Description>
              </div>
            </div>

            {user && (
              <div className="space-y-3 pt-2">
                <div className="space-y-1">
                  <Label className="text-xs uppercase tracking-wider text-muted-foreground">
                    Username
                  </Label>
                  <div className="font-mono text-sm p-2.5 bg-muted rounded-md border">
                    {user.username}
                  </div>
                </div>

                <div className="space-y-1">
                  <Label className="text-xs uppercase tracking-wider text-muted-foreground">
                    Palavra-passe
                  </Label>
                  <div className="flex items-center gap-2">
                    <div className="flex-1 font-mono text-sm p-2.5 bg-muted rounded-md border tracking-wider">
                      {showPassword ? user.password : "•".repeat(user.password.length)}
                    </div>
                    <button
                      type="button"
                      onClick={() => setShowPassword((v) => !v)}
                      className="p-2.5 border rounded-md hover:bg-muted transition-colors"
                      aria-label={showPassword ? "Esconder palavra-passe" : "Mostrar palavra-passe"}
                    >
                      {showPassword ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
                    </button>
                  </div>
                </div>
              </div>
            )}

            <div className="flex gap-2 pt-2">
              <Button type="button" variant="outline" className="flex-1" onClick={copyCredentials}>
                <Copy className="size-4 mr-2" />
                {copied ? "Copiado!" : "Copiar"}
              </Button>
              <Button type="button" className="flex-1" onClick={handleClose}>
                Fechar
              </Button>
            </div>
          </div>
        </DialogPrimitive.Content>
      </DialogPrimitive.Portal>
    </DialogPrimitive.Root>
  );
}
