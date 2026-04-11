import { renderHook, act, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import React from "react";
import { Provider } from "react-redux";
import { configureStore } from "@reduxjs/toolkit";
import formCacheReducer from "../store/formCacheSlice";
import { useDocumentForm } from "./useDocumentForm";
import { ApiError } from "../utils/appError";

/** テスト用の Redux Store を生成するヘルパー */
function createTestStore() {
  return configureStore({
    reducer: { formCache: formCacheReducer },
  });
}

/** テスト用のフォーム状態型 */
type TestForm = { title: string };

/** テスト用のレスポンス型 */
type TestResponse = { id: string; title: string };

/** Provider ラッパーを生成するヘルパー */
function makeWrapper(store: ReturnType<typeof createTestStore>) {
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return React.createElement(Provider, { store, children });
  };
}

describe("useDocumentForm", () => {
  const mockLoadLatest = vi.fn();
  const mockCreateDocument = vi.fn();
  const mockUpdateDocument = vi.fn();
  const mockBuildPayload = vi.fn();
  const mockMapResponseToForm = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    mockBuildPayload.mockImplementation((form: TestForm) => ({ title: form.title }));
    mockMapResponseToForm.mockImplementation((r: TestResponse): TestForm => ({
      title: r.title,
    }));
  });

  /** save() が API エラー（500）を返した場合、error メッセージが表示されること */
  it("save() で API エラーが発生した場合 error がセットされる", async () => {
    mockLoadLatest.mockRejectedValue(new Error("Not found"));

    const store = createTestStore();
    const { result } = renderHook(
      () =>
        useDocumentForm<TestForm, { title: string }, TestResponse>({
          createInitialForm: () => ({ title: "" }),
          loadLatest: mockLoadLatest,
          createDocument: mockCreateDocument,
          updateDocument: mockUpdateDocument,
          buildPayload: mockBuildPayload,
          mapResponseToForm: mockMapResponseToForm,
          successMessage: "保存しました",
        }),
      { wrapper: makeWrapper(store) },
    );

    // ローディング完了を待つ
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    // createDocument が 500 エラーを返すように設定
    mockCreateDocument.mockRejectedValueOnce(new Error("サーバーエラーが発生しました"));

    await act(async () => {
      await result.current.save();
    });

    expect(result.current.error).toBe("サーバーエラーが発生しました");
    expect(result.current.success).toBeNull();
  });

  /** save() が成功した場合、success メッセージが表示されること */
  it("save() が成功した場合 success がセットされる", async () => {
    mockLoadLatest.mockRejectedValue(new Error("Not found"));
    mockCreateDocument.mockResolvedValueOnce({ id: "new-id", title: "テスト" });

    const store = createTestStore();
    const { result } = renderHook(
      () =>
        useDocumentForm<TestForm, { title: string }, TestResponse>({
          createInitialForm: () => ({ title: "" }),
          loadLatest: mockLoadLatest,
          createDocument: mockCreateDocument,
          updateDocument: mockUpdateDocument,
          buildPayload: mockBuildPayload,
          mapResponseToForm: mockMapResponseToForm,
          successMessage: "保存しました",
        }),
      { wrapper: makeWrapper(store) },
    );

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    await act(async () => {
      await result.current.save();
    });

    expect(result.current.success).toBe("保存しました");
    expect(result.current.error).toBeNull();
  });

  /** save() が 401 ApiError を受け取った場合、error メッセージがセットされること */
  it("save() で 401 ApiError が発生した場合 error メッセージがセットされる", async () => {
    mockLoadLatest.mockRejectedValue(new Error("Not found"));
    mockCreateDocument.mockRejectedValueOnce(
      new ApiError({ code: "UNAUTHORIZED", message: "認証が必要です" }),
    );

    const store = createTestStore();
    const { result } = renderHook(
      () =>
        useDocumentForm<TestForm, { title: string }, TestResponse>({
          createInitialForm: () => ({ title: "" }),
          loadLatest: mockLoadLatest,
          createDocument: mockCreateDocument,
          updateDocument: mockUpdateDocument,
          buildPayload: mockBuildPayload,
          mapResponseToForm: mockMapResponseToForm,
          successMessage: "保存しました",
        }),
      { wrapper: makeWrapper(store) },
    );

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    await act(async () => {
      await result.current.save();
    });

    expect(result.current.error).toBe("認証が必要です");
    expect(result.current.success).toBeNull();
  });

  /** beforeSave でエラーがスローされた場合、API が呼ばれずエラーが表示されること */
  it("beforeSave でエラーがスローされた場合 API が呼ばれずエラーがセットされる", async () => {
    mockLoadLatest.mockRejectedValue(new Error("Not found"));

    const store = createTestStore();
    const { result } = renderHook(
      () =>
        useDocumentForm<TestForm, { title: string }, TestResponse>({
          createInitialForm: () => ({ title: "" }),
          loadLatest: mockLoadLatest,
          createDocument: mockCreateDocument,
          updateDocument: mockUpdateDocument,
          buildPayload: mockBuildPayload,
          mapResponseToForm: mockMapResponseToForm,
          successMessage: "保存しました",
          beforeSave: async () => {
            throw new Error("基本情報が未入力です");
          },
        }),
      { wrapper: makeWrapper(store) },
    );

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    await act(async () => {
      await result.current.save();
    });

    expect(result.current.error).toBe("基本情報が未入力です");
    expect(mockCreateDocument).not.toHaveBeenCalled();
  });
});
