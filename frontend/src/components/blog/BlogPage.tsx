import { useState, useEffect, useCallback } from "react";
import {
  getBlogAccounts,
  addBlogAccount,
  deleteBlogAccount,
  getBlogArticles,
  syncBlogAccount,
  summarizeBlogArticles,
} from "../../api";
import type { BlogAccount, BlogArticle } from "../../types";
import { ZennIcon } from "../icons/ZennIcon";
import { NoteIcon } from "../icons/NoteIcon";
import shared from "../../styles/shared.module.css";
import styles from "./BlogPage.module.css";

type PlatformFilter = "all" | "zenn" | "note";

/** 対応プラットフォーム定義 */
const PLATFORMS = [
  {
    key: "zenn" as const,
    label: "Zenn",
    urlPrefix: "https://zenn.dev/",
    icon: <ZennIcon size={22} />,
  },
  {
    key: "note" as const,
    label: "note",
    urlPrefix: "https://note.com/",
    icon: <NoteIcon size={22} />,
  },
] as const;

/**
 * ブログ連携ページ。固定プラットフォーム一覧でアカウント連携 → 記事一覧・AI分析。
 */
export function BlogPage() {
  const [accounts, setAccounts] = useState<BlogAccount[]>([]);
  const [articles, setArticles] = useState<BlogArticle[]>([]);
  const [filter, setFilter] = useState<PlatformFilter>("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // プラットフォームごとの入力中ユーザー名
  const [draftUsernames, setDraftUsernames] = useState<
    Record<string, string>
  >({ zenn: "", note: "" });

  // 保存中 / 同期中のプラットフォーム
  const [savingPlatform, setSavingPlatform] = useState<string | null>(null);
  const [syncingPlatform, setSyncingPlatform] = useState<string | null>(null);

  // AI分析
  const [summary, setSummary] = useState<string | null>(null);
  const [summaryLoading, setSummaryLoading] = useState(false);

  /** アカウント map（platform → account） */
  const accountMap = new Map(accounts.map((a) => [a.platform, a]));

  const loadData = useCallback(async () => {
    try {
      const accs = await getBlogAccounts();
      setAccounts(accs);
      if (accs.length > 0) {
        const arts = await getBlogArticles(
          filter === "all" ? undefined : filter,
        );
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

  /**
   * ユーザー名を保存（連携）し、自動で記事を同期する。
   */
  const handleSave = async (platform: "zenn" | "note") => {
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
      } catch {
        setSuccess("アカウントを連携しました。「同期」ボタンで記事を取得できます。");
      }
    } catch (e) {
      setError(
        e instanceof Error ? e.message : "アカウントの連携に失敗しました",
      );
    } finally {
      setSavingPlatform(null);
    }
  };

  /**
   * 記事を同期する。
   */
  const handleSync = async (platform: "zenn" | "note") => {
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
  const handleDelete = async (platform: "zenn" | "note") => {
    const account = accountMap.get(platform);
    if (!account) return;
    setError(null);
    setSuccess(null);
    try {
      await deleteBlogAccount(account.id);
      await loadData();
      setSuccess("アカウントを解除しました");
    } catch (e) {
      setError(
        e instanceof Error ? e.message : "アカウントの解除に失敗しました",
      );
    }
  };

  /**
   * AI分析を実行する。
   */
  const handleSummarize = async () => {
    if (articles.length === 0) return;
    setSummaryLoading(true);
    setSummary(null);
    setError(null);
    try {
      const result = await summarizeBlogArticles(articles);
      if (result.available) {
        setSummary(result.summary);
      } else {
        setError("AI分析サーバーに接続できません");
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "AI分析に失敗しました");
    } finally {
      setSummaryLoading(false);
    }
  };

  if (loading) {
    return (
      <>
        <div className={shared.pageHeader}>
          <h1>ブログ連携</h1>
        </div>
        <div className={shared.pageBody}>
          <p className={styles.emptyMessage}>読み込み中...</p>
        </div>
      </>
    );
  }

  return (
    <>
      <div className={shared.pageHeader}>
        <h1>ブログ連携</h1>
        <div className={shared.pageHeaderActions}>
          <button
            type="button"
            onClick={handleSummarize}
            disabled={articles.length === 0 || summaryLoading}
          >
            {summaryLoading ? "分析中..." : "AI分析"}
          </button>
        </div>
      </div>

      <div className={shared.pageBody}>
        {error && <p className={styles.errorMessage}>{error}</p>}
        {success && <p className={styles.successMessage}>{success}</p>}

        {/* プラットフォーム連携セクション */}
        <div className={styles.linkSection}>
          <h2>アウトプット連携</h2>

          <div className={styles.platformList}>
            {PLATFORMS.map((pf) => {
              const linked = accountMap.get(pf.key);
              return (
                <div key={pf.key} className={styles.platformRow}>
                  <div className={styles.platformIcon}>{pf.icon}</div>
                  <span className={styles.platformLabel}>{pf.label}</span>

                  {linked ? (
                    /* ── 連携済み ── */
                    <>
                      <span className={styles.urlPrefix}>{pf.urlPrefix}</span>
                      <span className={styles.linkedUsername}>
                        {linked.username}
                      </span>
                      <span className={styles.linkedBadge}>連携済み</span>
                      <button
                        type="button"
                        className={styles.actionButton}
                        disabled={syncingPlatform === pf.key}
                        onClick={() => handleSync(pf.key)}
                      >
                        {syncingPlatform === pf.key ? "同期中..." : "同期"}
                      </button>
                      <button
                        type="button"
                        className={styles.unlinkButton}
                        onClick={() => handleDelete(pf.key)}
                      >
                        解除
                      </button>
                    </>
                  ) : (
                    /* ── 未連携 ── */
                    <>
                      <span className={styles.urlPrefix}>{pf.urlPrefix}</span>
                      <input
                        type="text"
                        className={styles.usernameInput}
                        placeholder="ユーザー名"
                        value={draftUsernames[pf.key]}
                        onChange={(e) =>
                          setDraftUsernames((prev) => ({
                            ...prev,
                            [pf.key]: e.target.value,
                          }))
                        }
                        onKeyDown={(e) => {
                          if (e.key === "Enter") handleSave(pf.key);
                        }}
                      />
                      <button
                        type="button"
                        className={styles.saveButton}
                        disabled={
                          savingPlatform === pf.key ||
                          !draftUsernames[pf.key]?.trim()
                        }
                        onClick={() => handleSave(pf.key)}
                      >
                        {savingPlatform === pf.key ? "保存中..." : "保存"}
                      </button>
                    </>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* 記事一覧 */}
        {accounts.length > 0 && (
          <div className={styles.articleSection}>
            <div className={styles.articleHeader}>
              <h2>記事一覧</h2>
              <div className={styles.filterTabs}>
                {(["all", "zenn", "note"] as PlatformFilter[]).map((f) => (
                  <button
                    key={f}
                    type="button"
                    className={`${styles.filterTab} ${filter === f ? styles.filterTabActive : ""}`}
                    onClick={() => setFilter(f)}
                  >
                    {f === "all" ? "All" : f === "zenn" ? "Zenn" : "note"}
                  </button>
                ))}
              </div>
            </div>

            {articles.length === 0 ? (
              <p className={styles.emptyMessage}>
                記事がありません。「同期」ボタンで記事を取得してください。
              </p>
            ) : (
              <div className={styles.articleList}>
                {articles.map((art) => (
                  <a
                    key={art.id}
                    href={art.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className={styles.articleItem}
                  >
                    <div className={styles.articleTop}>
                      <span className={styles.articleIcon}>
                        {art.platform === "zenn" ? (
                          <ZennIcon size={16} />
                        ) : (
                          <NoteIcon size={16} />
                        )}
                      </span>
                      <span className={styles.articleTitle}>{art.title}</span>
                      <span className={styles.articleDate}>
                        {art.published_at}
                      </span>
                    </div>
                    <div className={styles.articleMeta}>
                      {art.likes_count > 0 && (
                        <span>いいね: {art.likes_count}</span>
                      )}
                      {art.tags.length > 0 && (
                        <span>タグ: {art.tags.join(", ")}</span>
                      )}
                      {art.summary && (
                        <span>
                          {art.summary.length > 80
                            ? `${art.summary.slice(0, 80)}...`
                            : art.summary}
                        </span>
                      )}
                    </div>
                  </a>
                ))}
              </div>
            )}
          </div>
        )}

        {/* AI 分析結果 */}
        {(summaryLoading || summary) && (
          <div className={styles.aiSection}>
            <h2>AI 分析結果</h2>
            {summaryLoading ? (
              <p className={styles.summaryLoading}>分析中...</p>
            ) : (
              <p className={styles.summaryText}>{summary}</p>
            )}
          </div>
        )}
      </div>
    </>
  );
}
