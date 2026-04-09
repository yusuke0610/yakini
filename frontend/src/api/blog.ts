import { request } from "./client";
import type { BlogAccount, BlogArticle } from "../types";
import type { TaskStatusResponse } from "./career-analysis";

export interface BlogScoreArticle {
  id: string;
  title: string;
  url: string;
  published_at: string | null;
  likes_count: number;
  tags: string[];
  is_tech: boolean;
}

export interface BlogScoreResponse {
  frequency_rank: string;
  reaction_rank: string;
  count_rank: string;
  overall_rank: string;
  tech_article_count: number;
  total_article_count: number;
  avg_monthly_posts: number;
  avg_likes: number;
  articles: BlogScoreArticle[];
}

export interface BlogSummaryResponse {
  summary: string;
  available: boolean;
  status?: string;
  error_message?: string;
  error_code?: string;
}

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
 * ブログ記事の AI サマリを生成する（202 非同期）。
 */
export function summarizeBlogArticles(
  articles: BlogArticle[],
): Promise<BlogSummaryResponse> {
  return request<BlogSummaryResponse>(
    "/api/blog/summarize",
    {
      method: "POST",
      body: JSON.stringify({ articles }),
    },
  );
}

/**
 * DB に保存されたブログ AI 分析結果を取得する。
 */
export function getBlogSummaryCache(): Promise<BlogSummaryResponse> {
  return request<BlogSummaryResponse>("/api/blog/summary-cache");
}

/**
 * サマリ生成ステータスを取得する（ポーリング用）。
 */
export function getBlogSummaryCacheStatus(): Promise<TaskStatusResponse> {
  return request<TaskStatusResponse>("/api/blog/summary-cache/status");
}

/**
 * ブログスコアリング結果を取得する。
 */
export function getBlogScore(): Promise<BlogScoreResponse> {
  return request<BlogScoreResponse>("/api/blog/score");
}
