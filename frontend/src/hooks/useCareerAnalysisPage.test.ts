import { renderHook, waitFor, act } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { useCareerAnalysisPage } from "./useCareerAnalysisPage";
import type { CareerAnalysisResponse } from "../api";

/** テスト用のダミー分析データ */
const dummyCompleted: CareerAnalysisResponse = {
  id: 1,
  version: 1,
  target_position: "SRE",
  status: "completed",
  result: {
    growth_summary: "成長中",
    tech_stack: { top: [], summary: "" },
    strengths: [],
    career_paths: [],
    action_items: [],
  },
  created_at: "2024-01-01T00:00:00",
};

const dummyPending: CareerAnalysisResponse = {
  id: 2,
  version: 2,
  target_position: "Backend",
  status: "pending",
  result: null,
  created_at: "2024-01-02T00:00:00",
};

/** ../api モジュール全体をモック */
vi.mock("../api", () => ({
  listAnalyses: vi.fn(),
  generateAnalysis: vi.fn(),
  deleteAnalysis: vi.fn(),
  getAnalysisStatus: vi.fn(),
  toAppError: vi.fn((e: unknown, fallback: string) => ({
    code: "INTERNAL_ERROR",
    message: e instanceof Error ? e.message : fallback,
    action: null,
    retryAfter: null,
    errorId: "test-error-id",
  })),
}));

describe("useCareerAnalysisPage", () => {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  let api: Record<string, any>;

  beforeEach(async () => {
    vi.clearAllMocks();
    api = await import("../api");
    api.listAnalyses.mockResolvedValue([]);
  });

  /** マウント時に listAnalyses が呼ばれ、データがなければ input フェーズになること */
  it("マウント時にデータなしの場合 input フェーズになる", async () => {
    api.listAnalyses.mockResolvedValue([]);

    const { result } = renderHook(() => useCareerAnalysisPage());

    await waitFor(() => {
      expect(result.current.phase).toBe("input");
    });

    expect(result.current.analyses).toEqual([]);
    expect(result.current.error).toBeNull();
  });

  /** マウント時にデータがあれば list フェーズになること */
  it("マウント時にデータありの場合 list フェーズになる", async () => {
    api.listAnalyses.mockResolvedValue([dummyCompleted]);

    const { result } = renderHook(() => useCareerAnalysisPage());

    await waitFor(() => {
      expect(result.current.phase).toBe("list");
    });

    expect(result.current.analyses).toEqual([dummyCompleted]);
  });

  /** マウント時に pending レコードがあればポーリングフェーズになること */
  it("マウント時に pending レコードがある場合 polling フェーズになる", async () => {
    api.listAnalyses.mockResolvedValue([dummyPending]);

    const { result } = renderHook(() => useCareerAnalysisPage());

    await waitFor(() => {
      expect(result.current.phase).toBe("polling");
    });
  });

  /** handleGenerate が失敗した場合、error がセットされ input フェーズになること */
  it("handleGenerate が失敗した場合 error がセットされ input フェーズになる", async () => {
    api.listAnalyses.mockResolvedValue([]);
    api.generateAnalysis.mockRejectedValue(new Error("生成に失敗しました"));

    const { result } = renderHook(() => useCareerAnalysisPage());

    await waitFor(() => {
      expect(result.current.phase).toBe("input");
    });

    await act(async () => {
      await result.current.handleGenerate("SRE");
    });

    expect(result.current.error).not.toBeNull();
    expect(result.current.error?.message).toBe("生成に失敗しました");
    expect(result.current.phase).toBe("input");
  });

  /** handleGenerate が成功した場合、polling フェーズに遷移すること */
  it("handleGenerate が成功した場合 polling フェーズに遷移する", async () => {
    api.listAnalyses.mockResolvedValue([]);
    api.generateAnalysis.mockResolvedValue({ id: 10, status: "pending" });

    const { result } = renderHook(() => useCareerAnalysisPage());

    await waitFor(() => {
      expect(result.current.phase).toBe("input");
    });

    await act(async () => {
      await result.current.handleGenerate("SRE");
    });

    expect(result.current.phase).toBe("polling");
  });

  /** handleDelete が成功した場合、削除後の一覧を返すこと */
  it("handleDelete が成功した場合 更新後の一覧を返す", async () => {
    api.listAnalyses.mockResolvedValue([dummyCompleted]);
    api.deleteAnalysis.mockResolvedValue(undefined);

    const { result } = renderHook(() => useCareerAnalysisPage());

    await waitFor(() => {
      expect(result.current.phase).toBe("list");
    });

    let updated: CareerAnalysisResponse[] | null = null;

    await act(async () => {
      updated = await result.current.handleDelete(1);
    });

    expect(api.deleteAnalysis).toHaveBeenCalledWith(1);
    expect(updated).toEqual([]);
    expect(result.current.analyses).toEqual([]);
  });

  /** handleDelete が失敗した場合、null を返し error がセットされること */
  it("handleDelete が失敗した場合 null を返し error がセットされる", async () => {
    api.listAnalyses.mockResolvedValue([dummyCompleted]);
    api.deleteAnalysis.mockRejectedValue(new Error("削除に失敗しました"));

    const { result } = renderHook(() => useCareerAnalysisPage());

    await waitFor(() => {
      expect(result.current.phase).toBe("list");
    });

    let updated: CareerAnalysisResponse[] | null = undefined as never;

    await act(async () => {
      updated = await result.current.handleDelete(1);
    });

    expect(updated).toBeNull();
    expect(result.current.error).not.toBeNull();
    expect(result.current.analyses).toEqual([dummyCompleted]);
  });
});
