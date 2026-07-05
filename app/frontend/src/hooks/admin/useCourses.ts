import { CourseService } from "@/services/course.service";
import type { CourseResponse } from "@/types/course";
import { usePaginatedResource } from "@/hooks/common/usePaginatedResource";

export function useCourses() {
  const resource = usePaginatedResource<CourseResponse>(
    CourseService.listAllCourses,
    (c, q) =>
      c.code.toLowerCase().includes(q) || c.name.toLowerCase().includes(q),
  );

  return {
    courses: resource.items,
    paginatedCourses: resource.paginatedItems,
    currentPage: resource.currentPage,
    setCurrentPage: resource.setCurrentPage,
    totalPages: resource.totalPages,
    loading: resource.loading,
    query: resource.query,
    setQuery: resource.setQuery,
    refresh: resource.refresh,
  };
}
