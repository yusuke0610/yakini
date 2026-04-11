import { test, expect } from "@playwright/test";

/**
 * 認証フロー E2E テスト
 */

test.describe("未認証ユーザー", () => {
  test("ルートへのアクセスは /login へリダイレクトされる", async ({ page }) => {
    let oauthRedirectUrl: string | null = null;

    // /auth/me が 401 を返す → 未認証扱い
    await page.route("**/auth/me", (route) =>
      route.fulfill({
        status: 401,
        contentType: "application/json",
        body: JSON.stringify({ detail: "Unauthorized" }),
      }),
    );
    await page.route("**/auth/github/login?*", (route) => {
      oauthRedirectUrl = route.request().url();
      return route.fulfill({
        status: 200,
        contentType: "text/html",
        body: "<html><body>mock oauth</body></html>",
      });
    });

    await page.goto("/");
    // App は /login 到達後に GitHub OAuth へ自動遷移するため、
    // /login を経由したことだけを先に待ち、その後 OAuth 開始を確認する。
    await page.waitForURL("**/login", { timeout: 5_000 });
    await expect.poll(() => oauthRedirectUrl).not.toBeNull();
    expect(oauthRedirectUrl).toContain("/auth/github/login");
    expect(oauthRedirectUrl).toContain("return_to=");
  });

  test("/career へ直接アクセスすると /login にリダイレクトされる", async ({ page }) => {
    let oauthRedirectUrl: string | null = null;

    await page.route("**/auth/me", (route) =>
      route.fulfill({
        status: 401,
        contentType: "application/json",
        body: JSON.stringify({ detail: "Unauthorized" }),
      }),
    );
    await page.route("**/auth/github/login?*", (route) => {
      oauthRedirectUrl = route.request().url();
      return route.fulfill({
        status: 200,
        contentType: "text/html",
        body: "<html><body>mock oauth</body></html>",
      });
    });

    await page.goto("/career");
    await page.waitForURL("**/login", { timeout: 5_000 });
    await expect.poll(() => oauthRedirectUrl).not.toBeNull();
    expect(oauthRedirectUrl).toContain("/auth/github/login");
    expect(oauthRedirectUrl).toContain("return_to=");
  });
});
