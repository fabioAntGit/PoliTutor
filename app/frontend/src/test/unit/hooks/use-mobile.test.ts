import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook } from "@testing-library/react";
import { useIsMobile } from "@/hooks/common/use-mobile";

beforeEach(() => {
  window.matchMedia = vi.fn().mockReturnValue({
    matches: false,
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
  });
});

describe("useIsMobile", () => {
  it("returns true when the viewport is below the mobile breakpoint", () => {
    window.innerWidth = 500;
    const { result } = renderHook(() => useIsMobile());
    expect(result.current).toBe(true);
  });

  it("returns false when the viewport is at or above the breakpoint", () => {
    window.innerWidth = 1200;
    const { result } = renderHook(() => useIsMobile());
    expect(result.current).toBe(false);
  });
});
