import * as coursesApi from "@/api/courses";
import type { CourseResponse } from "@/types/course";

export const CourseService = {
  listCourses: coursesApi.listCourses,
  listAllCourses: coursesApi.listAllCourses,
  createCourse: coursesApi.createCourse,
  updateCourse: coursesApi.updateCourse,
  deleteCourse: coursesApi.deleteCourse,

  async listMyCourses(myCourseCodes: string[]): Promise<CourseResponse[]> {
    const mine = new Set(myCourseCodes);
    const courses = await coursesApi.listCourses();
    return courses.filter((course) => mine.has(course.code));
  },
};
