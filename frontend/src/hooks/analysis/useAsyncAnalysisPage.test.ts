import { renderHook, act, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { useAsyncAnalysisPage } from "./useAsyncAnalysisPage";

describe("useAsyncAnalysisPage", () => {
  const mockLoadCache = vi.fn();
  const mockCheckStatus = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  /** 初回マウント時にキャッシュが存在する場合、result フェーズに遷移すること */
  it("キャッシュが存在する場合 result フェーズに遷移する", async () => {
    mockLoadCache.mockResolvedValue({ result: { id: "test-result" } });
    mockCheckStatus.mockResolvedValue({ status: "completed" });

    const { result } = renderHook(() =>
      useAsyncAnalysisPage({
        loadCache: mockLoadCache,
        checkStatus: mockCheckStatus,
      }),
    );

    await waitFor(() => {
      expect(result.current.phase).toBe("result");
    });

    expect(result.current.result).toEqual({ id: "test-result" });
  });

  /** 初回マウント時にキャッシュが存在しない場合、input フェーズに遷移すること */
  it("キャッシュが存在しない場合 input フェーズに遷移する", async () => {
    mockLoadCache.mockResolvedValue({ result: null });
    mockCheckStatus.mockResolvedValue({ status: "idle" });

    const { result } = renderHook(() =>
      useAsyncAnalysisPage({
        loadCache: mockLoadCache,
        checkStatus: mockCheckStatus,
      }),
    );

    await waitFor(() => {
      expect(result.current.phase).toBe("input");
    });

    expect(result.current.result).toBeNull();
  });

  /** 初回マウント時に status が pending の場合、polling フェーズに遷移すること */
  it("status が pending の場合 polling フェーズに遷移する", async () => {
    mockLoadCache.mockResolvedValue({ result: null, status: "pending" });
    // ポーリングが止まらないよう pending を返し続ける
    mockCheckStatus.mockResolvedValue({ status: "pending" });

    const { result } = renderHook(() =>
      useAsyncAnalysisPage({
        loadCache: mockLoadCache,
        checkStatus: mockCheckStatus,
      }),
    );

    await waitFor(() => {
      expect(result.current.phase).toBe("polling");
    });
  });

  /** ポーリングで status: "dead_letter" を返した場合、input フェーズに戻ること */
  it("ポーリングで status が dead_letter の場合 input フェーズに戻る", async () => {
    // 初回は pending → polling フェーズに遷移
    mockLoadCache.mockResolvedValue({ result: null, status: "pending" });
    // ポーリング中に dead_letter を返す
    mockCheckStatus.mockResolvedValue({
      status: "dead_letter",
      error_message: "分析に失敗しました",
    });

    const { result } = renderHook(() =>
      useAsyncAnalysisPage({
        loadCache: mockLoadCache,
        checkStatus: mockCheckStatus,
      }),
    );

    await waitFor(() => {
      expect(result.current.phase).toBe("input");
    });

    expect(result.current.error).toEqual(
      expect.objectContaining({
        code: "INTERNAL_ERROR",
        message: "分析に失敗しました",
      }),
    );
  });

  /** transitionToPolling を呼ぶと polling フェーズに遷移すること */
  it("transitionToPolling を呼ぶと polling フェーズに遷移する", async () => {
    mockLoadCache.mockResolvedValue({ result: null });
    mockCheckStatus.mockResolvedValue({ status: "pending" });

    const { result } = renderHook(() =>
      useAsyncAnalysisPage({
        loadCache: mockLoadCache,
        checkStatus: mockCheckStatus,
      }),
    );

    // input フェーズになるまで待つ
    await waitFor(() => {
      expect(result.current.phase).toBe("input");
    });

    act(() => {
      result.current.transitionToPolling();
    });

    expect(result.current.phase).toBe("polling");
  });

  /** backToInput を呼ぶと input フェーズに戻り result がリセットされること */
  it("backToInput を呼ぶと input フェーズに戻り result がリセットされる", async () => {
    mockLoadCache.mockResolvedValue({ result: { id: "existing" } });
    mockCheckStatus.mockResolvedValue({ status: "completed" });

    const { result } = renderHook(() =>
      useAsyncAnalysisPage({
        loadCache: mockLoadCache,
        checkStatus: mockCheckStatus,
      }),
    );

    await waitFor(() => {
      expect(result.current.phase).toBe("result");
    });

    act(() => {
      result.current.backToInput();
    });

    expect(result.current.phase).toBe("input");
    expect(result.current.result).toBeNull();
  });

  /** loadCache でエラーが発生した場合、input フェーズに遷移すること */
  it("loadCache でエラーが発生した場合 input フェーズに遷移する", async () => {
    mockLoadCache.mockRejectedValue(new Error("ネットワークエラー"));
    mockCheckStatus.mockResolvedValue({ status: "idle" });

    const { result } = renderHook(() =>
      useAsyncAnalysisPage({
        loadCache: mockLoadCache,
        checkStatus: mockCheckStatus,
      }),
    );

    await waitFor(() => {
      expect(result.current.phase).toBe("input");
    });
  });
});
