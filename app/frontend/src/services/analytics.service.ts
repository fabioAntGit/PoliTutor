import * as analyticsApi from "@/api/analytics";
import type {
  OverviewRead,
  ActivityRead,
  CoursesRead,
  CourseOverviewRead,
  CourseTopicsRead,
  CourseSourcesRead,
} from "@/types/analytics";

export const AnalyticsService = {
  async getOverview(): Promise<OverviewRead> {
    return analyticsApi.getOverview();
  },

  async getActivity(range: "7d" | "30d" | "90d"): Promise<ActivityRead> {
    return analyticsApi.getActivity(range);
  },

  async getCourses(): Promise<CoursesRead> {
    return analyticsApi.getCourses();
  },

  async getCourseOverview(course: string): Promise<CourseOverviewRead> {
    return analyticsApi.getCourseOverview(course);
  },

  async getCourseActivity(course: string, range: "7d" | "30d" | "90d"): Promise<ActivityRead> {
    return analyticsApi.getCourseActivity(course, range);
  },

  async getCourseTopics(course: string): Promise<CourseTopicsRead> {
    return analyticsApi.getCourseTopics(course);
  },

  async getCourseSources(course: string): Promise<CourseSourcesRead> {
    return analyticsApi.getCourseSources(course);
  },
};
