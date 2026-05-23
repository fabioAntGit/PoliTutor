import { describe, it, expect, vi, beforeEach } from "vitest";
import { api } from "@/api/client";
import * as analytics from "@/api/analytics";

vi.mock("@/api/client", () => ({ api: { get: vi.fn() } }));

const get = vi.mocked(api.get);

describe("analytics API", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("getOverview hits the overview endpoint", async () => {
    get.mockResolvedValue({ data: { total_conversations: 1 } });
    const result = await analytics.getOverview();
    expect(get).toHaveBeenCalledWith("/analytics/overview");
    expect(result.total_conversations).toBe(1);
  });

  it("getCourses hits the courses endpoint", async () => {
    get.mockResolvedValue({ data: { data: [] } });
    await analytics.getCourses();
    expect(get).toHaveBeenCalledWith("/analytics/courses");
  });

  it("getActivity passes the range as a query param", async () => {
    get.mockResolvedValue({ data: { data: [] } });
    await analytics.getActivity("7d");
    expect(get).toHaveBeenCalledWith("/analytics/activity", { params: { range: "7d" } });
  });

  it("getCourseOverview URL-encodes the course name", async () => {
    get.mockResolvedValue({ data: {} });
    await analytics.getCourseOverview("Algoritmos & Dados");
    expect(get).toHaveBeenCalledWith("/analytics/courses/Algoritmos%20%26%20Dados/overview");
  });

  it("getCourseActivity encodes the course and passes the range", async () => {
    get.mockResolvedValue({ data: { data: [] } });
    await analytics.getCourseActivity("ED 1", "90d");
    expect(get).toHaveBeenCalledWith(
      "/analytics/courses/ED%201/activity",
      { params: { range: "90d" } },
    );
  });

  it("getCourseTopics targets the topics endpoint", async () => {
    get.mockResolvedValue({ data: { course: "ED", topics: [] } });
    await analytics.getCourseTopics("ED");
    expect(get).toHaveBeenCalledWith("/analytics/courses/ED/topics");
  });

  it("getCourseSources targets the sources endpoint", async () => {
    get.mockResolvedValue({ data: { course: "ED", sources: [] } });
    await analytics.getCourseSources("ED");
    expect(get).toHaveBeenCalledWith("/analytics/courses/ED/sources");
  });
});
