import { test, expect } from "@playwright/test";

/**
 * 認証フロー E2E テスト
 */

test.describe("未認証ユーザー", () => {
  test("ルートへのアクセスは /login へリダイレクトされる", async ({ page }) => {
    await page.route("**/auth/me", (route) =>
      route.fulfill({
        status: 401,
        contentType: "application/json",
        body: JSON.stringify({ detail: "Unauthorized" }),
      }),
    );

    await page.goto("/");
    await page.waitForURL("**/login", { timeout: 5_000 });

    // ログインボタンが表示されることを確認する
    await expect(page.getByRole("button", { name: "GitHubでログイン" })).toBeVisible();
  });

  test("/career へ直接アクセスすると /login にリダイレクトされる", async ({ page }) => {
    await page.route("**/auth/me", (route) =>
      route.fulfill({
        status: 401,
        contentType: "application/json",
        body: JSON.stringify({ detail: "Unauthorized" }),
      }),
    );

    await page.goto("/career");
    await page.waitForURL("**/login", { timeout: 5_000 });

    await expect(page.getByRole("button", { name: "GitHubでログイン" })).toBeVisible();
  });

  test("GitHubでログインボタンを押すと /auth/github/login-url が呼ばれる", async ({ page }) => {
    let loginUrlRequest: string | null = null;

    await page.route("**/auth/me", (route) =>
      route.fulfill({
        status: 401,
        contentType: "application/json",
        body: JSON.stringify({ detail: "Unauthorized" }),
      }),
    );

    await page.route("**/auth/github/login-url*", (route) => {
      loginUrlRequest = route.request().url();
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          authorization_url: "http://localhost:5173/mock-github-oauth",
          state: "mock-state",
        }),
      });
    });

    // mock OAuth URL への遷移を止める
    await page.route("**/mock-github-oauth*", (route) =>
      route.fulfill({
        status: 200,
        contentType: "text/html",
        body: "<html><body>mock oauth</body></html>",
      }),
    );

    await page.goto("/login");
    await page.waitForURL("**/login", { timeout: 5_000 });

    await page.getByRole("button", { name: "GitHubでログイン" }).click();
    await expect.poll(() => loginUrlRequest).not.toBeNull();
    expect(loginUrlRequest).toContain("/auth/github/login-url");
    expect(loginUrlRequest).toContain("return_to=");
  });
});
