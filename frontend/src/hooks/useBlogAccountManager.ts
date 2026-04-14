import { useState, useEffect, useCallback } from "react";

import {
  getBlogAccounts,
  addBlogAccount,
  deleteBlogAccount,
  getBlogArticles,
  syncBlogAccount,
} from "../api";
import type { BlogAccount, BlogArticle } from "../types";
import { useBlogSummaryPolling } from "./useBlogSummaryPolling";

type PlatformKey = "zenn" | "note" | "qiita";

/**
 * BlogPage のブログアカウント管理・同期・AI分析ロジックを提供するカスタムフック。
 */
export function useBlogAccountManager(filter: "all" | "zenn" | "note" | "qiita") {
  const [accounts, setAccounts] = useState<BlogAccount[]>([]);
  const [articles, setArticles] = useState<BlogArticle[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  /** プラットフォームごとの入力中ユーザー名 */
  const [draftUsernames, setDraftUsernames] = useState<Record<string, string>>({
    zenn: "",
    note: "",
    qiita: "",
  });

  /** 保存中のプラットフォーム */
  const [savingPlatform, setSavingPlatform] = useState<string | null>(null);
  /** 同期中のプラットフォーム */
  const [syncingPlatform, setSyncingPlatform] = useState<string | null>(null);

  /** アカウント map（platform → account） */
  const accountMap = new Map(accounts.map((a) => [a.platform, a]));

  /**
   * アカウント一覧と記事一覧を再取得する。
   */
  const loadData = useCallback(async () => {
    try {
      const fetchedAccounts = await getBlogAccounts();
      setAccounts(fetchedAccounts);
      if (fetchedAccounts.length > 0) {
        const arts = await getBlogArticles(filter === "all" ? undefined : filter);
        setArticles(arts);
      } else {
        setArticles([]);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "データの取得に失敗しました");
    } finally {
      setLoading(false);
    }
  }, [filter]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const { summary, summaryLoading, summaryError, handleSummarize } =
    useBlogSummaryPolling(articles);

  /**
   * ユーザー名を保存（連携）し、自動で記事を同期する。
   */
  const handleSave = async (platform: PlatformKey) => {
    const username = draftUsernames[platform]?.trim();
    if (!username) return;
    setSavingPlatform(platform);
    setError(null);
    setSuccess(null);
    try {
      const account = await addBlogAccount(platform, username);
      setDraftUsernames((prev) => ({ ...prev, [platform]: "" }));
      await loadData();
      // 連携直後に自動同期
      try {
        const result = await syncBlogAccount(account.id);
        await loadData();
        setSuccess(
          `${result.synced_count}件の記事を取得しました（合計: ${result.total_count}件）`,
        );
      } catch (syncErr) {
        setSuccess("アカウントを連携しました");
        setError(
          syncErr instanceof Error
            ? syncErr.message
            : "記事の同期に失敗しました。「同期」ボタンで再試行してください。",
        );
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "アカウントの連携に失敗しました");
    } finally {
      setSavingPlatform(null);
    }
  };

  /**
   * 記事を同期する。
   */
  const handleSync = async (platform: PlatformKey) => {
    const account = accountMap.get(platform);
    if (!account) return;
    setSyncingPlatform(platform);
    setError(null);
    setSuccess(null);
    try {
      const result = await syncBlogAccount(account.id);
      await loadData();
      setSuccess(
        `${result.synced_count}件の新しい記事を取得しました（合計: ${result.total_count}件）`,
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : "同期に失敗しました");
    } finally {
      setSyncingPlatform(null);
    }
  };

  /**
   * アカウントを解除する。
   */
  const handleDelete = async (platform: PlatformKey) => {
    const account = accountMap.get(platform);
    if (!account) return;
    setError(null);
    setSuccess(null);
    try {
      await deleteBlogAccount(account.id);
      await loadData();
      setSuccess("アカウントを解除しました");
    } catch (e) {
      setError(e instanceof Error ? e.message : "アカウントの解除に失敗しました");
    }
  };

  return {
    accounts,
    articles,
    loading,
    error: error || summaryError,
    success,
    draftUsernames,
    setDraftUsernames,
    savingPlatform,
    syncingPlatform,
    summary,
    summaryLoading,
    accountMap,
    handleSave,
    handleSync,
    handleDelete,
    handleSummarize,
  };
}
