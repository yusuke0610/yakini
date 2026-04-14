import { useState } from "react";

import { useBlogAccountManager } from "../../hooks/useBlogAccountManager";
import { ZennIcon } from "../icons/ZennIcon";
import { NoteIcon } from "../icons/NoteIcon";
import { QiitaIcon } from "../icons/QiitaIcon";
import { BlogScoreCard } from "./BlogScoreCard";
import { BlogAnalysisSection } from "./BlogAnalysisSection";
import { InlineSpinner } from "../ui/InlineSpinner";
import shared from "../../styles/shared.module.css";
import styles from "./BlogPage.module.css";

type PlatformFilter = "all" | "zenn" | "note" | "qiita";

const ARTICLES_PER_PAGE = 5;

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
  {
    key: "qiita" as const,
    label: "Qiita",
    urlPrefix: "https://qiita.com/",
    icon: <QiitaIcon size={22} />,
  },
] as const;

/**
 * ブログ連携ページ。固定プラットフォーム一覧でアカウント連携 → 記事一覧・AI分析。
 */
export function BlogPage() {
  const [filter, setFilter] = useState<PlatformFilter>("all");
  const [pageByFilter, setPageByFilter] = useState<Record<PlatformFilter, number>>({
    all: 1,
    zenn: 1,
    note: 1,
    qiita: 1,
  });

  const {
    accounts,
    articles,
    loading,
    error,
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
  } = useBlogAccountManager(filter);

  const totalPages = Math.max(1, Math.ceil(articles.length / ARTICLES_PER_PAGE));
  const currentPage = Math.min(pageByFilter[filter], totalPages);
  const showPagination = articles.length > ARTICLES_PER_PAGE;
  const pageStartIndex = (currentPage - 1) * ARTICLES_PER_PAGE;
  const visibleArticles = articles.slice(
    pageStartIndex,
    pageStartIndex + ARTICLES_PER_PAGE,
  );

  if (loading) {
    return (
      <>
        <div className={shared.pageHeader}>
          <h1>ブログ連携</h1>
        </div>
        <div className={shared.pageBody}>
          <InlineSpinner label="読み込み中..." />
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

        {/* ブログスコア */}
        {articles.length > 0 && <BlogScoreCard />}

        {/* 記事一覧 */}
        {accounts.length > 0 && (
          <div className={styles.articleSection}>
            <div className={styles.articleHeader}>
              <h2>記事一覧</h2>
              <div className={styles.filterTabs}>
                {(["all", "zenn", "note", "qiita"] as PlatformFilter[]).map((f) => (
                  <button
                    key={f}
                    type="button"
                    className={`${styles.filterTab} ${filter === f ? styles.filterTabActive : ""}`}
                    onClick={() => {
                      if (filter === f) return;
                      setFilter(f);
                      setPageByFilter((prev) => ({
                        ...prev,
                        [f]: 1,
                      }));
                    }}
                  >
                    {f === "all" ? "All" : f === "zenn" ? "Zenn" : f === "note" ? "note" : "Qiita"}
                  </button>
                ))}
              </div>
            </div>

            {articles.length === 0 ? (
              <p className={styles.emptyMessage}>
                記事がありません。「同期」ボタンで記事を取得してください。
              </p>
            ) : (
              <>
                <div className={styles.articleList}>
                  {visibleArticles.map((art) => (
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
                          ) : art.platform === "qiita" ? (
                            <QiitaIcon size={16} />
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

                {showPagination && (
                  <div className={styles.pagination}>
                    <button
                      type="button"
                      className={styles.paginationButton}
                      onClick={() =>
                        setPageByFilter((prev) => ({
                          ...prev,
                          [filter]: Math.max(1, currentPage - 1),
                        }))
                      }
                      disabled={currentPage === 1}
                    >
                      前へ
                    </button>
                    <span className={styles.pageIndicator}>
                      {currentPage} / {totalPages}
                    </span>
                    <button
                      type="button"
                      className={styles.paginationButton}
                      onClick={() =>
                        setPageByFilter((prev) => ({
                          ...prev,
                          [filter]: Math.min(totalPages, currentPage + 1),
                        }))
                      }
                      disabled={currentPage === totalPages}
                    >
                      次へ
                    </button>
                  </div>
                )}
              </>
            )}
          </div>
        )}

        {/* AI 分析結果 */}
        <BlogAnalysisSection summaryLoading={summaryLoading} summary={summary} />
      </div>
    </>
  );
}
