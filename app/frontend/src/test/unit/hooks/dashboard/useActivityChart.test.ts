import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor, act } from "@testing-library/react";
import { useActivityChart } from "@/hooks/dashboard/useActivityChart";
import { AnalyticsService } from "@/services/analytics.service";
import { useIsMobile } from "@/hooks/common/use-mobile";

vi.mock("@/services/analytics.service");
vi.mock("@/hooks/common/use-mobile", () => ({ useIsMobile: vi.fn(() => false) }));

const service = vi.mocked(AnalyticsService);

describe("useActivityChart", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useIsMobile).mockReturnValue(false);
  });

  it("fetches global activity with the default 30d range", async () => {
    service.getActivity.mockResolvedValue({ data: [{ date: "2026-01-01", questions: 2 }] });

    const { result } = renderHook(() => useActivityChart());

    await waitFor(() => expect(result.current.chartData).not.toBeNull());
    expect(result.current.timeRange).toBe("30d");
    expect(service.getActivity).toHaveBeenCalledWith("30d");
  });

  it("uses the course-scoped endpoint when a course is given", async () => {
    service.getCourseActivity.mockResolvedValue({ data: [] });

    const { result } = renderHook(() => useActivityChart("Math"));

    await waitFor(() => expect(result.current.chartData).not.toBeNull());
    expect(service.getCourseActivity).toHaveBeenCalledWith("Math", "30d");
    expect(service.getActivity).not.toHaveBeenCalled();
  });

  it("forces the 7d range on mobile", async () => {
    vi.mocked(useIsMobile).mockReturnValue(true);
    service.getActivity.mockResolvedValue({ data: [] });

    const { result } = renderHook(() => useActivityChart());

    await waitFor(() => expect(result.current.timeRange).toBe("7d"));
  });

  it("refetches when the range changes", async () => {
    service.getActivity.mockResolvedValue({ data: [] });

    const { result } = renderHook(() => useActivityChart());
    await waitFor(() => expect(result.current.chartData).not.toBeNull());

    act(() => result.current.setTimeRange("7d"));

    await waitFor(() => expect(service.getActivity).toHaveBeenCalledWith("7d"));
  });

  it("falls back to an empty dataset on error", async () => {
    service.getActivity.mockRejectedValue(new Error("boom"));

    const { result } = renderHook(() => useActivityChart());

    await waitFor(() => expect(result.current.chartData).toEqual([]));
  });
});
