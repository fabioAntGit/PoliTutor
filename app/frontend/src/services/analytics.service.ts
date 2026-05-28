import * as analyticsApi from "@/api/analytics";
import type {
  OverviewData,
  ActivityData,
  CoursesData,
  CourseOverview,
  CourseTopicsData,
  CourseSourcesData,
} from "@/api/analytics";

export const AnalyticsService = {
  async getOverview(): Promise<OverviewData> {
    return analyticsApi.getOverview();
  },

  async getActivity(range: "7d" | "30d" | "90d"): Promise<ActivityData> {
    return analyticsApi.getActivity(range);
  },

  async getCourses(): Promise<CoursesData> {
    return analyticsApi.getCourses();
  },

  async getCourseOverview(course: string): Promise<CourseOverview> {
    return analyticsApi.getCourseOverview(course);
  },

  async getCourseActivity(course: string, range: "7d" | "30d" | "90d"): Promise<ActivityData> {
    return analyticsApi.getCourseActivity(course, range);
  },

  async getCourseTopics(course: string): Promise<CourseTopicsData> {
    return analyticsApi.getCourseTopics(course);
  },

  async getCourseSources(course: string): Promise<CourseSourcesData> {
    return analyticsApi.getCourseSources(course);
  },
};
