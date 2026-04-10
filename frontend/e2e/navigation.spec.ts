import { test, expect } from "@playwright/test";
import { setupAuth, waitForAuthenticatedLayout } from "./helpers/auth";

/**
 * サイドバーナビゲーション E2E テスト
 */

test.describe("認証済みユーザーのナビゲーション", () => {
  test.beforeEach(async ({ page }) => {
    await setupAuth(page);
  });

  test("サイドバーが表示される", async ({ page }) => {
    await page.goto("/basic_info");
    await waitForAuthenticatedLayout(page);

    await expect(page.getByText("DevForge")).toBeVisible();
    await expect(page.getByRole("link", { name: "基本情報" })).toBeVisible();
    await expect(page.getByRole("link", { name: "職務経歴書" })).toBeVisible();
    await expect(page.getByRole("link", { name: "履歴書" })).toBeVisible();
    await expect(page.getByRole("link", { name: "GitHub分析" })).toBeVisible();
    await expect(page.getByRole("link", { name: "ブログ連携" })).toBeVisible();
    await expect(page.getByRole("link", { name: "キャリア分析" })).toBeVisible();
  });

  test("通知ベルがサイドバーに表示される", async ({ page }) => {
    await page.goto("/basic_info");
    await waitForAuthenticatedLayout(page);
    await expect(page.getByRole("button", { name: /通知/ })).toBeVisible();
  });

  test("ページ間のナビゲーションが動作する", async ({ page }) => {
    // BasicInfoForm のデータ取得をモック（空レスポンスで OK）
    await page.route("**/api/basic_info", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(null),
      }),
    );

    await page.goto("/basic_info");
    await waitForAuthenticatedLayout(page);

    await page.getByRole("link", { name: "職務経歴書" }).click();
    await expect(page).toHaveURL(/\/career/);
  });
});
