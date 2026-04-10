import { test, expect } from "@playwright/test";

/**
 * 認証フロー E2E テスト
 */

test.describe("未認証ユーザー", () => {
  test("ルートへのアクセスは /login へリダイレクトされる", async ({ page }) => {
    // /auth/me が 401 を返す → 未認証扱い
    await page.route("**/auth/me", (route) =>
      route.fulfill({ status: 401, body: JSON.stringify({ detail: "Unauthorized" }) }),
    );

    await page.goto("/");
    // App が authLoading=false になるまで待つ
    await page.waitForURL("**/login", { timeout: 5_000 });
    await expect(page).toHaveURL(/\/login/);
  });

  test("/basic_info へ直接アクセスすると /login にリダイレクトされる", async ({ page }) => {
    await page.route("**/auth/me", (route) =>
      route.fulfill({ status: 401, body: JSON.stringify({ detail: "Unauthorized" }) }),
    );

    await page.goto("/basic_info");
    await page.waitForURL("**/login", { timeout: 5_000 });
    await expect(page).toHaveURL(/\/login/);
  });
});
