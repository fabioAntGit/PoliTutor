import { useEffect, useState } from "react";
import { toast } from "sonner";

import { listCourses } from "@/api/courses";
import { deleteMemory as deleteMemoryRequest, listMemories } from "@/api/memory";
import type { UserMemory } from "@/api/memory";
import { authService } from "@/services/auth.service";
import { ApiError } from "@/lib/errors";
import type { CourseResponse } from "@/types/course";

export function useMemories() {
  const [courses, setCourses] = useState<CourseResponse[]>([]);
  const [selectedCourse, setSelectedCourse] = useState<string>("");
  const [memories, setMemories] = useState<UserMemory[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingMemories, setLoadingMemories] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  useEffect(() => {
    listCourses()
      .then((coursesData) => {
        const myCourses = new Set(authService.getCourses());
        const mine = coursesData.filter((c) => myCourses.has(c.code));
        setCourses(mine);
        if (mine.length > 0) {
          setSelectedCourse(mine[0].code);
        }
      })
      .catch(() => {
        setError("Não foi possível carregar as cadeiras. Tente novamente mais tarde.");
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  useEffect(() => {
    if (!selectedCourse) {
      setMemories([]);
      return;
    }

    let active = true;
    setLoadingMemories(true);
    listMemories(selectedCourse)
      .then((data) => {
        if (active) setMemories(data.memories);
      })
      .catch(() => {
        if (active) toast.error("Não foi possível carregar as memórias.");
      })
      .finally(() => {
        if (active) setLoadingMemories(false);
      });

    return () => {
      active = false;
    };
  }, [selectedCourse]);

  const deleteMemory = async (memId: string) => {
    setDeletingId(memId);
    try {
      await deleteMemoryRequest(memId);
      setMemories((prev) => prev.filter((m) => m.id !== memId));
      toast.success("Memória removida.");
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Erro ao remover a memória.";
      toast.error(message);
    } finally {
      setDeletingId(null);
    }
  };

  return {
    courses,
    selectedCourse,
    setSelectedCourse,
    memories,
    loading,
    loadingMemories,
    error,
    deletingId,
    deleteMemory,
  };
}
