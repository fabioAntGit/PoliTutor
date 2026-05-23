import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { useSidebarCourses } from "@/hooks/dashboard/useSidebarCourses";
import { AnalyticsService } from "@/services/analytics.service";

vi.mock("@/services/analytics.service");

const service = vi.mocked(AnalyticsService);

describe("useSidebarCourses", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("stores the course list returned by the service", async () => {
    service.getCourses.mockResolvedValue({ data: ["Math", "Physics"] });

    const { result } = renderHook(() => useSidebarCourses());

    await waitFor(() => expect(result.current.courses).toEqual(["Math", "Physics"]));
  });

  it("falls back to an empty list when the request fails", async () => {
    service.getCourses.mockRejectedValue(new Error("boom"));

    const { result } = renderHook(() => useSidebarCourses());

    await waitFor(() => expect(result.current.courses).toEqual([]));
  });
});
