import { useEffect, useMemo, useState, type ReactNode } from "react";
import { Dialog as DialogPrimitive } from "radix-ui";
import { Brain, KeyRound, UserRound, X, type LucideIcon } from "lucide-react";

import { cn } from "@/lib/utils";
import { authService } from "@/services/auth.service";
import type { UserRole } from "@/types/user";
import { MemoriesSection } from "@/components/settings/memories-section";
import { PasswordSection } from "@/components/settings/password-section";
import { AccountSection } from "@/components/settings/account-section";

export type SettingsSectionId = "memories" | "password" | "account";

interface SettingsSection {
  id: SettingsSectionId;
  label: string;
  icon: LucideIcon;
  roles?: UserRole[];
  render: () => ReactNode;
}

// Adicionar novas secções de definições = juntar uma entrada a esta lista.
const SECTIONS: SettingsSection[] = [
  {
    id: "memories",
    label: "Memórias",
    icon: Brain,
    roles: ["student"],
    render: () => <MemoriesSection />,
  },
  {
    id: "password",
    label: "Palavra-passe",
    icon: KeyRound,
    render: () => <PasswordSection />,
  },
  {
    id: "account",
    label: "Conta",
    icon: UserRound,
    render: () => <AccountSection />,
  },
];

interface SettingsDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  initialSection?: SettingsSectionId;
}

export function SettingsDialog({
  open,
  onOpenChange,
  initialSection = "memories",
}: SettingsDialogProps) {
  const role = authService.getRole();

  const sections = useMemo(
    () => SECTIONS.filter((s) => !s.roles || (role && s.roles.includes(role as UserRole))),
    [role],
  );

  const [activeId, setActiveId] = useState<SettingsSectionId>(initialSection);

  // Ao abrir, posicionar na secção pedida (caindo na primeira disponível).
  useEffect(() => {
    if (!open) return;
    const wanted = sections.find((s) => s.id === initialSection);
    setActiveId(wanted ? wanted.id : sections[0]?.id ?? "password");
  }, [open, initialSection, sections]);

  const active = sections.find((s) => s.id === activeId) ?? sections[0];

  return (
    <DialogPrimitive.Root open={open} onOpenChange={onOpenChange}>
      <DialogPrimitive.Portal>
        <DialogPrimitive.Overlay className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm" />
        <DialogPrimitive.Content className="fixed left-1/2 top-1/2 z-50 flex h-[80vh] max-h-[640px] w-[calc(100%-2rem)] max-w-3xl -translate-x-1/2 -translate-y-1/2 overflow-hidden rounded-2xl border bg-background shadow-xl">
          <DialogPrimitive.Title className="sr-only">Definições</DialogPrimitive.Title>

          {/* Navegação lateral */}
          <nav className="hidden w-52 shrink-0 flex-col gap-1 border-r bg-muted/30 p-2 sm:flex">
            <p className="px-3 pb-1 pt-2 text-xs font-medium text-muted-foreground">
              Definições
            </p>
            {sections.map((section) => {
              const Icon = section.icon;
              const isActive = section.id === active?.id;
              return (
                <button
                  key={section.id}
                  type="button"
                  onClick={() => setActiveId(section.id)}
                  className={cn(
                    "flex items-center gap-2.5 rounded-lg px-3 py-2 text-left text-sm transition-colors",
                    isActive
                      ? "bg-muted font-medium text-foreground"
                      : "text-muted-foreground hover:bg-muted/60 hover:text-foreground",
                  )}
                >
                  <Icon className="size-4 shrink-0" />
                  {section.label}
                </button>
              );
            })}
          </nav>

          {/* Painel de conteúdo */}
          <div className="flex min-w-0 flex-1 flex-col">
            <header className="flex shrink-0 items-center justify-between gap-2 border-b px-5 py-3.5">
              <div className="flex items-center gap-2 text-sm">
                <span className="text-muted-foreground">Definições</span>
                <span className="text-muted-foreground/50">/</span>
                <span className="font-medium">{active?.label}</span>
              </div>
              <DialogPrimitive.Close className="flex size-8 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-muted hover:text-foreground">
                <X className="size-4" />
                <span className="sr-only">Fechar</span>
              </DialogPrimitive.Close>
            </header>

            {/* Seletor de secção em ecrãs pequenos (sem sidebar) */}
            <div className="flex gap-1 border-b px-3 py-2 sm:hidden">
              {sections.map((section) => (
                <button
                  key={section.id}
                  type="button"
                  onClick={() => setActiveId(section.id)}
                  className={cn(
                    "rounded-lg px-3 py-1.5 text-sm transition-colors",
                    section.id === active?.id
                      ? "bg-muted font-medium"
                      : "text-muted-foreground hover:bg-muted/60",
                  )}
                >
                  {section.label}
                </button>
              ))}
            </div>

            <div className="flex-1 overflow-y-auto p-5">{active?.render()}</div>
          </div>
        </DialogPrimitive.Content>
      </DialogPrimitive.Portal>
    </DialogPrimitive.Root>
  );
}
