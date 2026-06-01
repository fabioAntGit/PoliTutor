import { useState } from "react";
import { useLocation, useNavigate } from "react-router";
import {
  Brain,
  ChevronsUpDown,
  KeyRound,
  LayoutDashboard,
  LogOut,
  Moon,
  Shield,
  Sun,
  Trash2,
} from "lucide-react";

import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { DeleteAccountDialog } from "@/components/account/delete-account-dialog";
import { useTheme } from "@/components/theme/theme-provider";
import { authService } from "@/services/auth.service";
import { logout } from "@/api/auth";

function initialsFor(name: string | null, fallback: string | null): string {
  const source = name?.trim() || fallback?.trim() || "?";
  const parts = source.split(/\s+/).filter(Boolean);
  const letters = parts.length >= 2 ? parts[0][0] + parts[parts.length - 1][0] : source.slice(0, 2);
  return letters.toUpperCase();
}

export function UserMenu({ compact = false }: { compact?: boolean } = {}) {
  const navigate = useNavigate();
  const { pathname } = useLocation();
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === "dark";
  const fullName = authService.getFullName();
  const username = authService.getUsername();
  const role = authService.getRole();
  const isAdmin = role === "admin";
  const isStudent = role === "student";
  const onAdminPage = pathname.startsWith("/admin");
  const onDashboardPage = pathname.startsWith("/dashboard");
  const [deleteOpen, setDeleteOpen] = useState(false);

  const handleLogout = async () => {
    const accessToken = authService.getAccessToken();
    if (accessToken) {
      await logout(accessToken).catch(() => {});
    }
    authService.clearTokens();
    navigate("/login", { replace: true });
  };

  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          {compact ? (
            <button
              type="button"
              aria-label="Conta"
              className="flex items-center justify-center rounded-full outline-none transition-shadow ring-ring/50 hover:ring-3 focus-visible:ring-3 aria-expanded:ring-3"
            >
              <Avatar size="default">
                <AvatarFallback>{initialsFor(fullName, username)}</AvatarFallback>
              </Avatar>
            </button>
          ) : (
            <button
              type="button"
              className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-left transition-colors hover:bg-muted aria-expanded:bg-muted"
            >
              <Avatar size="sm">
                <AvatarFallback>{initialsFor(fullName, username)}</AvatarFallback>
              </Avatar>
              <div className="grid flex-1 leading-tight">
                <span className="truncate text-sm font-medium">
                  {fullName ?? username ?? "Conta"}
                </span>
                {role && (
                  <span className="truncate text-[11px] text-muted-foreground capitalize">
                    {role}
                  </span>
                )}
              </div>
              <ChevronsUpDown className="size-4 text-muted-foreground" />
            </button>
          )}
        </DropdownMenuTrigger>
        <DropdownMenuContent
          align="end"
          side={compact ? "bottom" : "top"}
          sideOffset={6}
          className="min-w-56"
        >
          <DropdownMenuLabel className="font-normal">
            <div className="grid leading-tight">
              <span className="truncate text-sm font-medium text-foreground">
                {fullName ?? "Conta"}
              </span>
              {username && (
                <span className="truncate text-xs text-muted-foreground">
                  {username}
                </span>
              )}
            </div>
          </DropdownMenuLabel>
          <DropdownMenuSeparator />
          <DropdownMenuItem
            onSelect={(event) => {
              event.preventDefault();
              toggleTheme();
            }}
          >
            {isDark ? <Sun /> : <Moon />}
            {isDark ? "Modo claro" : "Modo escuro"}
          </DropdownMenuItem>
          {isStudent && (
            <DropdownMenuItem onSelect={() => navigate("/memories")}>
              <Brain />
              Memórias guardadas
            </DropdownMenuItem>
          )}
          <DropdownMenuItem onSelect={() => navigate("/change-password")}>
            <KeyRound />
            Alterar password
          </DropdownMenuItem>
          {isAdmin && !onAdminPage && (
            <DropdownMenuItem onSelect={() => navigate("/admin")}>
              <Shield />
              Dashboard admin
            </DropdownMenuItem>
          )}
          {isAdmin && !onDashboardPage && (
            <DropdownMenuItem onSelect={() => navigate("/dashboard")}>
              <LayoutDashboard />
              Dashboard cadeiras
            </DropdownMenuItem>
          )}
          <DropdownMenuSeparator />
          <DropdownMenuItem
            variant="destructive"
            onSelect={() => setDeleteOpen(true)}
          >
            <Trash2 />
            Eliminar conta
          </DropdownMenuItem>
          <DropdownMenuItem onSelect={handleLogout}>
            <LogOut />
            Terminar sessão
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      <DeleteAccountDialog open={deleteOpen} onOpenChange={setDeleteOpen} />
    </>
  );
}
