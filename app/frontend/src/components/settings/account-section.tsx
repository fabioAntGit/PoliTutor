import { useState } from "react";

import { Button } from "@/components/ui/button";
import { DeleteAccountDialog } from "@/components/account/delete-account-dialog";

export function AccountSection() {
  const [deleteOpen, setDeleteOpen] = useState(false);

  return (
    <div className="space-y-4">
      <p className="text-[13px] leading-relaxed text-muted-foreground">
        Faça a gestão da sua conta.
      </p>

      <div className="rounded-2xl border border-destructive/30 bg-destructive/5 p-5">
        <h3 className="text-sm font-semibold text-foreground">Eliminar conta</h3>
        <p className="mt-1 text-[13px] leading-relaxed text-muted-foreground">
          Esta ação remove a sua conta, conversas e memória do tutor. Os dados
          ficam retidos durante 30 dias e depois são apagados de forma
          permanente.
        </p>
        <Button
          variant="destructive"
          className="mt-4 h-10 px-5 text-sm"
          onClick={() => setDeleteOpen(true)}
        >
          Eliminar conta
        </Button>
      </div>

      <DeleteAccountDialog open={deleteOpen} onOpenChange={setDeleteOpen} />
    </div>
  );
}
