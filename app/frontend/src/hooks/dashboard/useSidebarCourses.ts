import { useState, useEffect } from "react";
import { CourseService } from "@/services/course.service";
import type { CourseResponse } from "@/types/course";

export function useSidebarCourses() {
  const [courses, setCourses] = useState<CourseResponse[] | null>(null);

  useEffect(() => {
    CourseService.listCourses()
      .then(setCourses)
      .catch(() => setCourses([]));
  }, []);

  return { courses };
}
