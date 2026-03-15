import { request } from "./client";
import type { BlogAccount, BlogArticle } from "../types";

/**
 * 連携アカウント一覧を取得する。
 */
export function getBlogAccounts(): Promise<BlogAccount[]> {
  return request<BlogAccount[]>("/api/blog/accounts");
}

/**
 * 連携アカウントを登録する。
 */
export function addBlogAccount(
  platform: "zenn" | "note",
  username: string,
): Promise<BlogAccount> {
  return request<BlogAccount>("/api/blog/accounts", {
    method: "POST",
    body: JSON.stringify({ platform, username }),
  });
}

/**
 * 連携アカウントを解除する。
 */
export async function deleteBlogAccount(id: string): Promise<void> {
  await request<void>(`/api/blog/accounts/${id}`, {
    method: "DELETE",
  });
}

/**
 * DB の記事一覧を取得する。
 */
export function getBlogArticles(platform?: string): Promise<BlogArticle[]> {
  const query = platform ? `?platform=${platform}` : "";
  return request<BlogArticle[]>(`/api/blog/articles${query}`);
}

/**
 * 外部 API から記事を同期する。
 */
export function syncBlogAccount(
  accountId: string,
): Promise<{ synced_count: number; total_count: number }> {
  return request<{ synced_count: number; total_count: number }>(
    `/api/blog/accounts/${accountId}/sync`,
    { method: "POST" },
  );
}

/**
 * ブログ記事の AI サマリを生成する。
 */
export function summarizeBlogArticles(
  articles: BlogArticle[],
): Promise<{ summary: string; available: boolean }> {
  return request<{ summary: string; available: boolean }>(
    "/api/blog/summarize",
    {
      method: "POST",
      body: JSON.stringify({ articles }),
    },
  );
}
