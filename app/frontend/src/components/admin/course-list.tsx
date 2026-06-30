import { useState } from "react";
import { Search, Pencil, Loader2 } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useCourses } from "@/hooks/admin/useCourses";
import EditCourseDialog from "@/components/admin/edit-course-dialog";
import type { CourseResponse } from "@/types/course";

import {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationNext,
  PaginationPrevious,
} from "@/components/ui/pagination";

export default function CourseList() {
  const {
    courses,
    paginatedCourses,
    currentPage,
    setCurrentPage,
    totalPages,
    loading,
    query,
    setQuery,
    refresh,
  } = useCourses();
  const [editing, setEditing] = useState<CourseResponse | null>(null);

  return (
    <div className="space-y-4">
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
        <Input
          placeholder="Procurar por sigla ou nome"
          className="pl-9"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
      </div>

      {loading ? (
        <div className="flex justify-center py-8">
          <Loader2 className="size-5 animate-spin text-muted-foreground" />
        </div>
      ) : courses.length === 0 ? (
        <p className="text-sm text-muted-foreground text-center py-8">
          Nenhuma cadeira encontrada.
        </p>
      ) : (
        <div className="space-y-4">
          <div className="max-h-[60vh] overflow-y-auto space-y-2 pr-1">
            {paginatedCourses.map((course) => (
              <div
                key={course.id}
                className="flex items-center justify-between p-3 border rounded-lg hover:bg-muted/40 transition-colors"
              >
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-primary/10 text-primary font-medium uppercase tracking-wider font-mono">
                      {course.code}
                    </span>
                    <p className="text-sm font-medium truncate">{course.name}</p>
                    {!course.is_active && (
                      <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-muted text-muted-foreground font-medium uppercase tracking-wider">
                        Inativa
                      </span>
                    )}
                  </div>
                  {course.description && (
                    <p className="text-xs text-muted-foreground truncate mt-0.5">
                      {course.description}
                    </p>
                  )}
                </div>
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  onClick={() => setEditing(course)}
                  aria-label={`Editar ${course.code}`}
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

      <EditCourseDialog
        course={editing}
        onClose={() => setEditing(null)}
        onSaved={() => {
          setEditing(null);
          refresh();
        }}
      />
    </div>
  );
}
