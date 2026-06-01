import { useEffect, useState } from "react";
import { listUsers } from "@/api/users";
import { listCourses } from "@/api/courses";
import type { UserResponse } from "@/types/user";
import type { CourseResponse } from "@/types/course";
import { usePaginatedResource } from "@/hooks/common/usePaginatedResource";

export function useUsers() {
  const [courses, setCourses] = useState<CourseResponse[]>([]);

  useEffect(() => {
    listCourses().then(setCourses).catch(() => {});
  }, []);

  const resource = usePaginatedResource<UserResponse>(
    listUsers,
    (u, q) =>
      u.username.toLowerCase().includes(q) ||
      u.full_name.toLowerCase().includes(q) ||
      u.email.toLowerCase().includes(q),
  );

  return {
    users: resource.items,
    paginatedUsers: resource.paginatedItems,
    currentPage: resource.currentPage,
    setCurrentPage: resource.setCurrentPage,
    totalPages: resource.totalPages,
    courses,
    loading: resource.loading,
    query: resource.query,
    setQuery: resource.setQuery,
    refresh: resource.refresh,
  };
}
