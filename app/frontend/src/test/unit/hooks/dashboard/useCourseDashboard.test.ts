import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { useCourseDashboard } from "@/hooks/dashboard/useCourseDashboard";
import { AnalyticsService } from "@/services/analytics.service";
import { useParams } from "react-router";

vi.mock("@/services/analytics.service");
vi.mock("react-router", () => ({ useParams: vi.fn(), useNavigate: () => vi.fn() }));

const service = vi.mocked(AnalyticsService);
const params = vi.mocked(useParams);

describe("useCourseDashboard", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("marks the course valid and loads overview, topics and sources", async () => {
    params.mockReturnValue({ courseId: "Math" });
    service.getCourses.mockResolvedValue({ data: ["Math"] });
    service.getCourseOverview.mockResolvedValue({
      course: "Math",
      total_conversations: 1,
      active_students: 1,
      total_messages: 1,
      avg_questions_per_conversation: 1,
    });
    service.getCourseTopics.mockResolvedValue({
      course: "Math",
      topics: [{ topic: "loops", count: 2 }],
    });
    service.getCourseSources.mockResolvedValue({
      course: "Math",
      sources: [{ filename: "a.pdf", references: 1 }],
    });

    const { result } = renderHook(() => useCourseDashboard());

    await waitFor(() => expect(result.current.status).toBe("valid"));
    expect(result.current.overview?.course).toBe("Math");
    expect(result.current.overview?.total_conversations).toBe(1);
    expect(result.current.overview?.active_students).toBe(1);
    expect(result.current.overview?.total_messages).toBe(1);
    expect(result.current.overview?.avg_questions_per_conversation).toBe(1);
    expect(result.current.topicItems).toHaveLength(1);
    expect(result.current.sourceItems).toHaveLength(1);
  });

  it("marks the course not_found when it is not in the course list", async () => {
    params.mockReturnValue({ courseId: "Ghost" });
    service.getCourses.mockResolvedValue({ data: ["Math"] });

    const { result } = renderHook(() => useCourseDashboard());

    await waitFor(() => expect(result.current.status).toBe("not_found"));
  });

  it("marks the course not_found when the course list request fails", async () => {
    params.mockReturnValue({ courseId: "Math" });
    service.getCourses.mockRejectedValue(new Error("boom"));

    const { result } = renderHook(() => useCourseDashboard());

    await waitFor(() => expect(result.current.status).toBe("not_found"));
  });
});
