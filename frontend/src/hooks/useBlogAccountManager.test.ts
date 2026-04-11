import { renderHook, act, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { useBlogAccountManager } from "./useBlogAccountManager";
import type { BlogAccount, BlogArticle } from "../types";

/** テスト用のダミーアカウントデータ */
const dummyAccounts: BlogAccount[] = [
  {
    id: "acc-1",
    platform: "zenn",
    username: "testuser",
    created_at: "2024-01-01T00:00:00",
  },
];

/** テスト用のダミー記事データ */
const dummyArticles: BlogArticle[] = [
  {
    id: "art-1",
    platform: "zenn",
    title: "テスト記事",
    url: "https://zenn.dev/testuser/articles/test",
    published_at: "2024-01-01",
    likes_count: 10,
    summary: null,
    tags: ["TypeScript"],
  },
];

/** ../api モジュール全体をモック */
vi.mock("../api", () => ({
  getBlogAccounts: vi.fn(),
  getBlogArticles: vi.fn(),
  addBlogAccount: vi.fn(),
  deleteBlogAccount: vi.fn(),
  syncBlogAccount: vi.fn(),
  summarizeBlogArticles: vi.fn(),
  getBlogSummaryCache: vi.fn(),
  getBlogSummaryCacheStatus: vi.fn(),
}));

describe("useBlogAccountManager", () => {
  // モック関数への参照を取得するために動的 import を使う
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  let api: Record<string, any>;

  beforeEach(async () => {
    vi.clearAllMocks();
    api = await import("../api");
    // デフォルトのモック戻り値を設定
    api.getBlogSummaryCache.mockResolvedValue({ available: false, summary: null, status: "idle" });
    api.getBlogSummaryCacheStatus.mockResolvedValue({ status: "idle" });
    api.getBlogAccounts.mockResolvedValue([]);
    api.getBlogArticles.mockResolvedValue([]);
  });

  /** マウント時に getBlogAccounts が呼ばれること */
  it("マウント時に getBlogAccounts が呼ばれる", async () => {
    api.getBlogAccounts.mockResolvedValue([]);

    renderHook(() => useBlogAccountManager("all"));

    await waitFor(() => {
      expect(api.getBlogAccounts).toHaveBeenCalledTimes(1);
    });
  });

  /** アカウントが存在する場合は getBlogArticles も呼ばれること */
  it("アカウントが存在する場合 getBlogArticles も呼ばれる", async () => {
    api.getBlogAccounts.mockResolvedValue(dummyAccounts);
    api.getBlogArticles.mockResolvedValue(dummyArticles);

    const { result } = renderHook(() => useBlogAccountManager("all"));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(api.getBlogArticles).toHaveBeenCalledTimes(1);
    expect(result.current.accounts).toEqual(dummyAccounts);
    expect(result.current.articles).toEqual(dummyArticles);
  });

  /** handleDelete を呼ぶと deleteBlogAccount が実行されデータが再取得されること */
  it("handleDelete を呼ぶと deleteBlogAccount が呼ばれデータが再取得される", async () => {
    api.getBlogAccounts.mockResolvedValue(dummyAccounts);
    api.getBlogArticles.mockResolvedValue(dummyArticles);
    api.deleteBlogAccount.mockResolvedValue(undefined);

    const { result } = renderHook(() => useBlogAccountManager("all"));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    // 削除後は accounts が空に
    api.getBlogAccounts.mockResolvedValue([]);

    await waitFor(async () => {
      await result.current.handleDelete("zenn");
    });

    expect(api.deleteBlogAccount).toHaveBeenCalledWith("acc-1");
    // 再取得が走ること
    await waitFor(() => {
      expect(api.getBlogAccounts).toHaveBeenCalledTimes(2);
    });
    expect(result.current.success).toBe("アカウントを解除しました");
  });

  /** getBlogAccounts がエラーの場合、error がセットされること */
  it("getBlogAccounts がエラーの場合 error がセットされる", async () => {
    api.getBlogAccounts.mockRejectedValue(new Error("ネットワークエラー"));

    const { result } = renderHook(() => useBlogAccountManager("all"));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.error).toBe("ネットワークエラー");
  });

  /**
   * addBlogAccount が成功し syncBlogAccount が失敗した場合、
   * success と error の両方がセットされること（部分成功）
   */
  it("addBlogAccount 成功 + syncBlogAccount 失敗の場合 success と error が両方セットされる", async () => {
    api.getBlogAccounts
      .mockResolvedValueOnce([])
      .mockResolvedValue(dummyAccounts);
    api.getBlogArticles.mockResolvedValue(dummyArticles);
    api.addBlogAccount.mockResolvedValue(dummyAccounts[0]);
    api.syncBlogAccount.mockRejectedValue(new Error("同期に失敗しました"));

    const { result } = renderHook(() => useBlogAccountManager("all"));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    await act(async () => {
      result.current.setDraftUsernames((prev) => ({ ...prev, zenn: "testuser" }));
    });

    await act(async () => {
      await result.current.handleSave("zenn");
    });

    // 連携成功メッセージが出ること
    expect(result.current.success).toBe("アカウントを連携しました");
    // 同期失敗エラーが出ること
    expect(result.current.error).toBe("同期に失敗しました");
  });
});
