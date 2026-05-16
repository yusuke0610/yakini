import { request } from "./client";
import { PATHS } from "./paths";
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
  return request<BlogAccount[]>(PATHS.blog.accounts);
}

/**
 * 連携アカウントを登録する。
 */
export function addBlogAccount(
  platform: "zenn" | "note" | "qiita",
  username: string,
): Promise<BlogAccount> {
  return request<BlogAccount>(PATHS.blog.accounts, {
    method: "POST",
    body: JSON.stringify({ platform, username }),
  });
}

/**
 * 連携アカウントの username を更新する。
 */
export function updateBlogAccount(
  platform: "zenn" | "note" | "qiita",
  username: string,
): Promise<BlogAccount> {
  return request<BlogAccount>(PATHS.blog.accountByPlatform(platform), {
    method: "PATCH",
    body: JSON.stringify({ username }),
  });
}

/**
 * 連携アカウントを解除する。
 */
export async function deleteBlogAccount(id: string): Promise<void> {
  await request<void>(PATHS.blog.accountById(id), {
    method: "DELETE",
  });
}

/**
 * DB の記事一覧を取得する。
 */
export function getBlogArticles(platform?: string): Promise<BlogArticle[]> {
  return request<BlogArticle[]>(PATHS.blog.articles(platform));
}

/**
 * 外部 API から記事を同期する。
 */
export function syncBlogAccount(
  accountId: string,
): Promise<{ synced_count: number; total_count: number }> {
  return request<{ synced_count: number; total_count: number }>(
    PATHS.blog.accountSync(accountId),
    { method: "POST" },
  );
}

/**
 * ブログ記事の AI サマリを生成する（202 非同期）。
 * 分析対象記事はサーバー側で DB から取得する。
 */
export function summarizeBlogArticles(): Promise<BlogSummaryResponse> {
  return request<BlogSummaryResponse>(PATHS.blog.summarize, { method: "POST" });
}

/**
 * 失敗したブログサマリタスクを手動で再実行する（202 非同期）。
 * 分析対象記事はサーバー側で DB から取得する。
 */
export function retrySummarizeBlogArticles(): Promise<BlogSummaryResponse> {
  return request<BlogSummaryResponse>(PATHS.blog.summarizeRetry, { method: "POST" });
}

/**
 * DB に保存されたブログ AI 分析結果を取得する。
 */
export function getBlogSummaryCache(): Promise<BlogSummaryResponse> {
  return request<BlogSummaryResponse>(PATHS.blog.summaryCache);
}

/**
 * サマリ生成ステータスを取得する（ポーリング用）。
 */
export function getBlogSummaryCacheStatus(): Promise<TaskStatusResponse> {
  return request<TaskStatusResponse>(PATHS.blog.summaryCacheStatus);
}

/**
 * ブログスコアリング結果を取得する。
 */
export function getBlogScore(): Promise<BlogScoreResponse> {
  return request<BlogScoreResponse>(PATHS.blog.score);
}
