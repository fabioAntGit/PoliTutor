import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { useDashboard } from "@/hooks/dashboard/useDashboard";
import { AnalyticsService } from "@/services/analytics.service";

vi.mock("@/services/analytics.service");

const service = vi.mocked(AnalyticsService);

describe("useDashboard", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("loads the overview and clears the loading flag", async () => {
    service.getOverview.mockResolvedValue({
      total_conversations: 5,
      active_students: 3,
      total_messages: 20,
      avg_questions_per_conversation: 4,
    });

    const { result } = renderHook(() => useDashboard());
    expect(result.current.loading).toBe(true);

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.overview?.total_conversations).toBe(5);
    expect(result.current.overview?.active_students).toBe(3);
    expect(result.current.overview?.total_messages).toBe(20);
    expect(result.current.overview?.avg_questions_per_conversation).toBe(4);
    expect(result.current.error).toBeNull();
  });

  it("exposes a error message when the request fails", async () => {
    service.getOverview.mockRejectedValue(new Error("network down"));

    const { result } = renderHook(() => useDashboard());

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.error).toBe("Não foi possível carregar os dados gerais.");
    expect(result.current.overview).toBeNull();
  });
});
