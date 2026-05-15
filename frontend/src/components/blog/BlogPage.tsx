import { useState } from "react";

import { useBlogAccountManager } from "../../hooks/useBlogAccountManager";
import { BlogScoreCard } from "./BlogScoreCard";
import { BlogAnalysisSection } from "./BlogAnalysisSection";
import { BlogPlatformList } from "./BlogPlatformList";
import { BlogArticleList } from "./BlogArticleList";
import { InlineSpinner } from "../ui/InlineSpinner";
import shared from "../../styles/shared.module.css";
import styles from "./BlogPage.module.css";

type PlatformFilter = "all" | "zenn" | "note" | "qiita";

/**
 * ブログ連携ページ。固定プラットフォーム一覧でアカウント連携 → 記事一覧・AI分析。
 */
export function BlogPage() {
  const [filter, setFilter] = useState<PlatformFilter>("all");

  const {
    accounts,
    articles,
    loading,
    accountError,
    summaryError,
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
        {accountError && <p className={styles.errorMessage}>{accountError}</p>}
        {summaryError && <p className={styles.errorMessage}>{summaryError}</p>}
        {success && <p className={styles.successMessage}>{success}</p>}

        <BlogPlatformList
          accountMap={accountMap}
          draftUsernames={draftUsernames}
          setDraftUsernames={setDraftUsernames}
          savingPlatform={savingPlatform}
          syncingPlatform={syncingPlatform}
          onSave={handleSave}
          onSync={handleSync}
          onDelete={handleDelete}
        />

        {articles.length > 0 && <BlogScoreCard />}

        {accounts.length > 0 && (
          <BlogArticleList
            articles={articles}
            filter={filter}
            onFilterChange={setFilter}
          />
        )}

        <BlogAnalysisSection summaryLoading={summaryLoading} summary={summary} />
      </div>
    </>
  );
}
