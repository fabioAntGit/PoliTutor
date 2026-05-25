import { useCallback, useEffect, useMemo, useState } from "react";
import { listAllCourses } from "@/api/courses";
import type { CourseResponse } from "@/types/course";

export function useCourses() {
  const [courses, setCourses] = useState<CourseResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const data = await listAllCourses();
      setCourses(data);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh().catch(() => setLoading(false));
  }, [refresh]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return courses;
    return courses.filter(
      (c) =>
        c.code.toLowerCase().includes(q) ||
        c.name.toLowerCase().includes(q),
    );
  }, [courses, query]);

  return { courses: filtered, loading, query, setQuery, refresh };
}
