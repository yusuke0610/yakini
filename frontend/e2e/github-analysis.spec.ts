import { test, expect } from "@playwright/test";
import { setupAuth, waitForAuthenticatedLayout } from "./helpers/auth";

/**
 * GitHub 分析ダッシュボードでの検出フレームワーク表示 E2E テスト（Issue #203）
 */

test.describe("GitHub 分析 - 検出フレームワーク表示", () => {
  test.beforeEach(async ({ page }) => {
    await setupAuth(page);
  });

  test("検出フレームワークが Frameworks セクションに表示される", async ({
    page,
  }) => {
    // 分析キャッシュのモックを登録（キャッチオールより後 = 優先される）
    await page.route("**/api/intelligence/cache", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          status: "completed",
          analysis_result: {
            username: "e2e-test-user",
            repos_analyzed: 3,
            unique_skills: 5,
            analyzed_at: "2026-04-24T00:00:00Z",
            languages: { TypeScript: 60000, Python: 40000 },
            detected_frameworks: ["React", "Next.js", "FastAPI"],
            position_scores: null,
          },
          position_advice: null,
        }),
      }),
    );

    await page.goto("/github_intelligence");
    await waitForAuthenticatedLayout(page);

    // ダッシュボードが表示されること
    await expect(
      page.getByRole("heading", { name: "e2e-test-user の分析結果" }),
    ).toBeVisible();

    // Frameworks セクションが存在し、各 framework 名が表示されること
    await expect(
      page.getByRole("heading", { name: "Frameworks" }),
    ).toBeVisible();
    const list = page.getByRole("list", { name: "検出フレームワーク一覧" });
    await expect(list).toBeVisible();
    await expect(list.getByText("React")).toBeVisible();
    await expect(list.getByText("Next.js")).toBeVisible();
    await expect(list.getByText("FastAPI")).toBeVisible();
  });

  test("検出フレームワークが空のとき Frameworks セクションが出ない", async ({
    page,
  }) => {
    await page.route("**/api/intelligence/cache", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          status: "completed",
          analysis_result: {
            username: "e2e-test-user",
            repos_analyzed: 1,
            unique_skills: 0,
            analyzed_at: "2026-04-24T00:00:00Z",
            languages: { TypeScript: 100 },
            detected_frameworks: [],
            position_scores: null,
          },
          position_advice: null,
        }),
      }),
    );

    await page.goto("/github_intelligence");
    await waitForAuthenticatedLayout(page);

    await expect(
      page.getByRole("heading", { name: "e2e-test-user の分析結果" }),
    ).toBeVisible();
    await expect(
      page.getByRole("heading", { name: "Frameworks" }),
    ).not.toBeVisible();
  });
});
