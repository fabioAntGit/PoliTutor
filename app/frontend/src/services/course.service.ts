import * as coursesApi from "@/api/courses";

export const CourseService = {
  listCourses: coursesApi.listCourses,
  listAllCourses: coursesApi.listAllCourses,
  listActiveCourses: coursesApi.listActiveCourses,
  createCourse: coursesApi.createCourse,
  updateCourse: coursesApi.updateCourse,
  deleteCourse: coursesApi.deleteCourse,
};
