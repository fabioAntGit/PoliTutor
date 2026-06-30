import * as analyticsApi from "@/api/analytics";
import type {
  OverviewRead,
  ActivityRead,
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

  async getCourseOverview(courseId: string): Promise<CourseOverviewRead> {
    return analyticsApi.getCourseOverview(courseId);
  },

  async getCourseActivity(courseId: string, range: "7d" | "30d" | "90d"): Promise<ActivityRead> {
    return analyticsApi.getCourseActivity(courseId, range);
  },

  async getCourseTopics(courseId: string): Promise<CourseTopicsRead> {
    return analyticsApi.getCourseTopics(courseId);
  },

  async getCourseSources(courseId: string): Promise<CourseSourcesRead> {
    return analyticsApi.getCourseSources(courseId);
  },
};
