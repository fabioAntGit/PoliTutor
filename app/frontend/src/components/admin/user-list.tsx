import { useState } from "react";
import { Search, Pencil, Loader2 } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useUsers } from "@/hooks/admin/useUsers";
import EditUserDialog from "@/components/admin/edit-user-dialog";
import type { UserResponse } from "@/types/user";

import {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationNext,
  PaginationPrevious,
} from "@/components/ui/pagination";

export default function UserList() {
  const {
    users,
    paginatedUsers,
    currentPage,
    setCurrentPage,
    totalPages,
    courses,
    loading,
    query,
    setQuery,
    refresh,
  } = useUsers();
  const [editing, setEditing] = useState<UserResponse | null>(null);
  const courseCodeById = new Map(courses.map((c) => [c.id, c.code] as const));

  return (
    <div className="space-y-4">
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
        <Input
          placeholder="Procurar por nome, username ou email"
          className="pl-9"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
      </div>

      {loading ? (
        <div className="flex justify-center py-8">
          <Loader2 className="size-5 animate-spin text-muted-foreground" />
        </div>
      ) : users.length === 0 ? (
        <p className="text-sm text-muted-foreground text-center py-8">
          Nenhum utilizador encontrado.
        </p>
      ) : (
        <div className="space-y-4">
          <div className="max-h-[60vh] overflow-y-auto space-y-2 pr-1">
            {paginatedUsers.map((user) => (
              <div
                key={user.username}
                className="flex items-center justify-between p-3 border rounded-lg hover:bg-muted/40 transition-colors"
              >
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <p className="text-sm font-medium truncate">{user.full_name}</p>
                    <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-primary/10 text-primary font-medium uppercase tracking-wider">
                      {user.role === "student" ? "Aluno" : user.role === "teacher" ? "Professor" : user.role}
                    </span>
                  </div>
                  <p className="text-xs text-muted-foreground truncate">{user.email}</p>
                  {user.courses.length > 0 && (
                    <p className="text-xs text-muted-foreground mt-0.5 font-mono uppercase">
                      {user.courses.map((id) => courseCodeById.get(id)).filter(Boolean).join(" · ")}
                    </p>
                  )}
                </div>
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  onClick={() => setEditing(user)}
                  aria-label={`Editar ${user.username}`}
                >
                  <Pencil className="size-4" />
                </Button>
              </div>
            ))}
          </div>

          {totalPages > 1 && (
            <Pagination>
              <PaginationContent>
                <PaginationItem>
                  <PaginationPrevious
                    href="#"
                    onClick={(e) => {
                      e.preventDefault();
                      setCurrentPage((p) => Math.max(1, p - 1));
                    }}
                    className={
                      currentPage === 1 ? "pointer-events-none opacity-50" : ""
                    }
                  />
                </PaginationItem>
                <PaginationItem>
                  <span className="text-sm font-medium px-4">
                    Página {currentPage} de {totalPages}
                  </span>
                </PaginationItem>
                <PaginationItem>
                  <PaginationNext
                    href="#"
                    onClick={(e) => {
                      e.preventDefault();
                      setCurrentPage((p) => Math.min(totalPages, p + 1));
                    }}
                    className={
                      currentPage === totalPages
                        ? "pointer-events-none opacity-50"
                        : ""
                    }
                  />
                </PaginationItem>
              </PaginationContent>
            </Pagination>
          )}
        </div>
      )}

      <EditUserDialog
        user={editing}
        courses={courses}
        onClose={() => setEditing(null)}
        onSaved={() => {
          setEditing(null);
          refresh();
        }}
      />
    </div>
  );
}
