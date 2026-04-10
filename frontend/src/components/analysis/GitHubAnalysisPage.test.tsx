import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect } from "vitest";
import { http, HttpResponse } from "msw";
import { server } from "../../test/mswServer";
import { GitHubAnalysisPage } from "./GitHubAnalysisPage";
import { renderWithProviders } from "../../test/renderWithProviders";

/** Provider 付きでレンダリングするヘルパー */
function renderPage() {
  return renderWithProviders(<GitHubAnalysisPage />);
}

describe("GitHubAnalysisPage", () => {
  it("キャッシュなしの場合、入力画面が表示される", async () => {
    server.use(
      http.get("*/api/intelligence/cache", () =>
        HttpResponse.json({
          analysis_result: null,
          position_advice: null,
          status: null,
        }),
      ),
    );

    renderPage();

    await waitFor(() => {
      expect(screen.getByText("分析開始")).toBeInTheDocument();
    });
    expect(screen.getByText("GitHub分析")).toBeInTheDocument();
  });

  it("キャッシュが存在する場合、結果画面が表示される", async () => {
    renderPage();

    await waitFor(() => {
      expect(
        screen.getByText("test-user-001 の分析結果"),
      ).toBeInTheDocument();
    });
    expect(screen.getByText("10")).toBeInTheDocument(); // repos_analyzed
    expect(screen.getByText("リポジトリ")).toBeInTheDocument();
  });

  it("分析開始ボタン押下後、ポーリング画面に遷移する", async () => {
    const user = userEvent.setup();

    server.use(
      http.get("*/api/intelligence/cache", () =>
        HttpResponse.json({
          analysis_result: null,
          position_advice: null,
          status: null,
        }),
      ),
      http.get("*/api/intelligence/cache/status", () =>
        HttpResponse.json({ status: "pending" }),
      ),
    );

    renderPage();

    await waitFor(() => {
      expect(screen.getByText("分析開始")).toBeInTheDocument();
    });

    await user.click(screen.getByText("分析開始"));

    await waitFor(() => {
      expect(
        screen.getByText("GitHubプロフィールを分析中..."),
      ).toBeInTheDocument();
    });
  });

  it("API 500 エラー時にエラーメッセージが表示される", async () => {
    const user = userEvent.setup();

    server.use(
      http.get("*/api/intelligence/cache", () =>
        HttpResponse.json({
          analysis_result: null,
          position_advice: null,
          status: null,
        }),
      ),
      http.post("*/api/intelligence/analyze", () =>
        HttpResponse.json(
          {
            code: "LLM_UNAVAILABLE",
            message: "AI 分析サービスが一時的に利用できません",
            error_id: "err-ui-500",
          },
          { status: 503 },
        ),
      ),
    );

    renderPage();

    await waitFor(() => {
      expect(screen.getByText("分析開始")).toBeInTheDocument();
    });

    await user.click(screen.getByText("分析開始"));

    await waitFor(() => {
      // エラーメッセージが表示されること（アプリがクラッシュしないこと）
      expect(screen.getByText(/AI 分析サービスが一時的に利用できません/)).toBeInTheDocument();
      expect(screen.getByText(/エラーID: err-ui-500/)).toBeInTheDocument();
    });
  });

  it("再分析ボタンで入力画面に戻る", async () => {
    const user = userEvent.setup();

    renderPage();

    await waitFor(() => {
      expect(
        screen.getByText("test-user-001 の分析結果"),
      ).toBeInTheDocument();
    });

    await user.click(screen.getByText("再分析"));

    await waitFor(() => {
      expect(screen.getByText("分析開始")).toBeInTheDocument();
    });
  });
});
