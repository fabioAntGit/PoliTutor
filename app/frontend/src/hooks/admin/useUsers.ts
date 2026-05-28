import { useEffect, useState, useMemo, useCallback } from "react";
import { listUsers } from "@/api/users";
import { listCourses } from "@/api/courses";
import type { UserResponse } from "@/types/user";
import type { CourseResponse } from "@/types/course";

export function useUsers() {
  const [users, setUsers] = useState<UserResponse[]>([]);
  const [courses, setCourses] = useState<CourseResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const [u, c] = await Promise.all([listUsers(), listCourses()]);
      setUsers(u);
      setCourses(c);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh().catch(() => setLoading(false));
  }, [refresh]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return users;
    return users.filter(
      (u) =>
        u.username.toLowerCase().includes(q) ||
        u.full_name.toLowerCase().includes(q) ||
        u.email.toLowerCase().includes(q),
    );
  }, [users, query]);

  return { users: filtered, courses, loading, query, setQuery, refresh };
}
