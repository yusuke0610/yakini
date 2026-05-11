import { renderHook, act, waitFor } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { useTaskPolling } from "./useTaskPolling";

/** ポーリング間隔を短くしてテストを高速化する */
const FAST_INTERVAL = 50;

describe("useTaskPolling", () => {
  it("completed になったとき onCompleted が呼ばれる", async () => {
    const onCompleted = vi.fn();
    const onFailed = vi.fn();
    const checkStatus = vi
      .fn()
      .mockResolvedValue({ status: "completed" });

    const { result } = renderHook(() =>
      useTaskPolling({
        checkStatus,
        onCompleted,
        onFailed,
        intervalMs: FAST_INTERVAL,
      }),
    );

    act(() => {
      result.current.startPolling();
    });

    await waitFor(() => {
      expect(onCompleted).toHaveBeenCalledOnce();
    });
    expect(onFailed).not.toHaveBeenCalled();
    expect(result.current.isPolling).toBe(false);
  });

  it("dead_letter になったとき onFailed が呼ばれる", async () => {
    const onCompleted = vi.fn();
    const onFailed = vi.fn();
    const checkStatus = vi.fn().mockResolvedValue({
      status: "dead_letter",
      error_message: "LLM タイムアウト",
    });

    const { result } = renderHook(() =>
      useTaskPolling({
        checkStatus,
        onCompleted,
        onFailed,
        intervalMs: FAST_INTERVAL,
      }),
    );

    act(() => {
      result.current.startPolling();
    });

    await waitFor(() => {
      expect(onFailed).toHaveBeenCalledWith(
        expect.objectContaining({
          code: "INTERNAL_ERROR",
          message: "LLM タイムアウト",
        }),
      );
    });
    expect(onCompleted).not.toHaveBeenCalled();
    expect(result.current.isPolling).toBe(false);
  });

  it("dead_letter で error_message がない場合デフォルトメッセージが渡される", async () => {
    const onFailed = vi.fn();
    const checkStatus = vi
      .fn()
      .mockResolvedValue({ status: "dead_letter" });

    const { result } = renderHook(() =>
      useTaskPolling({
        checkStatus,
        onCompleted: vi.fn(),
        onFailed,
        intervalMs: FAST_INTERVAL,
      }),
    );

    act(() => {
      result.current.startPolling();
    });

    await waitFor(() => {
      expect(onFailed).toHaveBeenCalledWith(
        expect.objectContaining({
          code: "INTERNAL_ERROR",
          message: "処理に失敗しました",
        }),
      );
    });
  });

  it("pending 中はポーリングが継続し completed で停止する", async () => {
    const onCompleted = vi.fn();
    const checkStatus = vi
      .fn()
      .mockResolvedValueOnce({ status: "pending" })
      .mockResolvedValueOnce({ status: "pending" })
      .mockResolvedValue({ status: "completed" });

    const { result } = renderHook(() =>
      useTaskPolling({
        checkStatus,
        onCompleted,
        onFailed: vi.fn(),
        intervalMs: FAST_INTERVAL,
      }),
    );

    act(() => {
      result.current.startPolling();
    });

    await waitFor(() => {
      expect(onCompleted).toHaveBeenCalledOnce();
    });
    // 少なくとも3回呼ばれている（pending, pending, completed）
    expect(checkStatus.mock.calls.length).toBeGreaterThanOrEqual(3);
  });

  it("アンマウント時にポーリングが停止する", async () => {
    const checkStatus = vi
      .fn()
      .mockResolvedValue({ status: "pending" });
    const onCompleted = vi.fn();

    const { result, unmount } = renderHook(() =>
      useTaskPolling({
        checkStatus,
        onCompleted,
        onFailed: vi.fn(),
        intervalMs: FAST_INTERVAL,
      }),
    );

    act(() => {
      result.current.startPolling();
    });

    // 初回ポーリングを待つ
    await waitFor(() => {
      expect(checkStatus).toHaveBeenCalled();
    });

    const callCount = checkStatus.mock.calls.length;
    unmount();

    // アンマウント後は呼び出し回数が増えないことを確認
    await new Promise((r) => setTimeout(r, FAST_INTERVAL * 3));
    expect(checkStatus.mock.calls.length).toBe(callCount);
  });

  it("ネットワークエラー時はポーリングが継続する", async () => {
    const onCompleted = vi.fn();
    const checkStatus = vi
      .fn()
      .mockRejectedValueOnce(new Error("Network error"))
      .mockResolvedValue({ status: "completed" });

    const { result } = renderHook(() =>
      useTaskPolling({
        checkStatus,
        onCompleted,
        onFailed: vi.fn(),
        intervalMs: FAST_INTERVAL,
      }),
    );

    act(() => {
      result.current.startPolling();
    });

    await waitFor(() => {
      expect(onCompleted).toHaveBeenCalledOnce();
    });
    // エラー後にリトライして completed に到達
    expect(checkStatus.mock.calls.length).toBeGreaterThanOrEqual(2);
  });
});
