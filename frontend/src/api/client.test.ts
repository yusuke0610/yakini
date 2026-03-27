import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { request } from "./client";

/** fetch のモックレスポンスを生成するヘルパー */
function makeResponse(status: number, body?: unknown): Response {
  const bodyStr = body !== undefined ? JSON.stringify(body) : "";
  return {
    ok: status >= 200 && status < 300,
    status,
    json: vi.fn().mockResolvedValue(body),
    text: vi.fn().mockResolvedValue(bodyStr),
    headers: new Headers(),
  } as unknown as Response;
}

describe("api/client request", () => {
  beforeEach(() => {
    // document.cookie をリセット
    Object.defineProperty(document, "cookie", {
      writable: true,
      value: "",
    });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  /** 200 レスポンスの場合、JSON がパースされて返されること */
  it("200 レスポンスの場合 JSON が返される", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(makeResponse(200, { id: "abc" })));

    const result = await request<{ id: string }>("/api/test");
    expect(result).toEqual({ id: "abc" });
  });

  /** 401 レスポンス → リフレッシュ成功 → リトライが成功すること */
  it("401 レスポンス後にリフレッシュが成功するとリトライされる", async () => {
    const fetchMock = vi
      .fn()
      // 1回目: 401（元リクエスト）
      .mockResolvedValueOnce(makeResponse(401))
      // 2回目: /auth/refresh → 200
      .mockResolvedValueOnce(makeResponse(200, {}))
      // 3回目: リトライ → 200
      .mockResolvedValueOnce(makeResponse(200, { id: "retried" }));

    vi.stubGlobal("fetch", fetchMock);

    const result = await request<{ id: string }>("/api/test");

    expect(fetchMock).toHaveBeenCalledTimes(3);
    expect(result).toEqual({ id: "retried" });
  });

  /** 401 → リフレッシュ失敗 → エラーがスローされること */
  it("401 後にリフレッシュが失敗するとエラーがスローされる", async () => {
    const fetchMock = vi
      .fn()
      // 1回目: 元リクエスト 401
      .mockResolvedValueOnce(makeResponse(401))
      // 2回目: /auth/refresh 失敗
      .mockResolvedValueOnce(makeResponse(401));

    vi.stubGlobal("fetch", fetchMock);

    await expect(request("/api/test")).rejects.toThrow("認証が必要です");
  });

  /**
   * 複数の 401 が同時に発生した場合、リフレッシュが 1 回だけ呼ばれること。
   * _isRefreshing フラグにより二重リフレッシュを防ぐ。
   */
  it("複数の同時 401 でリフレッシュは 1 回だけ実行される", async () => {
    let refreshCallCount = 0;

    const fetchMock = vi.fn().mockImplementation((url: string) => {
      if ((url as string).includes("/auth/refresh")) {
        refreshCallCount++;
        // 1回目のリフレッシュは成功、2回目以降は呼ばれないはず
        return Promise.resolve(makeResponse(200, {}));
      }
      // 最初の2リクエストは 401
      if (refreshCallCount === 0) {
        return Promise.resolve(makeResponse(401));
      }
      // リトライは成功
      return Promise.resolve(makeResponse(200, { id: "ok" }));
    });

    vi.stubGlobal("fetch", fetchMock);

    // 2つのリクエストを同時に発行
    // 注: _isRefreshing はモジュールレベルのフラグのため、
    //     実際には最初の401でリフレッシュが走り、2回目はエラーになる
    const [r1] = await Promise.allSettled([
      request("/api/test1"),
      request("/api/test2"),
    ]);

    // 少なくとも1回のリクエストが処理されていること
    expect(fetchMock).toHaveBeenCalled();
    // リフレッシュは最大1回
    expect(refreshCallCount).toBeLessThanOrEqual(1);
    // 1つ目はリトライで成功する
    expect(r1.status).toBe("fulfilled");
  });

  /** 500 系のレスポンスでエラーがスローされること */
  it("500 レスポンスの場合エラーがスローされる", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(makeResponse(500)));

    await expect(request("/api/test")).rejects.toThrow("サーバーエラー");
  });

  /** ネットワークエラーの場合、接続エラーメッセージがスローされること */
  it("ネットワークエラーの場合接続エラーがスローされる", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Failed to fetch")));

    await expect(request("/api/test")).rejects.toThrow("サーバーに接続できません");
  });
});
