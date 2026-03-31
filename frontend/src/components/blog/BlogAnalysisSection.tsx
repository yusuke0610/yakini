import styles from "./BlogPage.module.css";

/** BlogAnalysisSection のプロパティ型 */
type BlogAnalysisSectionProps = {
  /** AI 分析実行中フラグ */
  summaryLoading: boolean;
  /** AI 分析結果テキスト */
  summary: string | null;
};

/**
 * BlogPage の AI 分析結果セクション。
 * summaryLoading または summary がある場合のみ表示する。
 */
export function BlogAnalysisSection({ summaryLoading, summary }: BlogAnalysisSectionProps) {
  if (!summaryLoading && !summary) return null;

  return (
    <div className={styles.aiSection}>
      <h2>AI 分析結果</h2>
      {summaryLoading ? (
        <>
          <p className={styles.summaryLoading}>分析中...</p>
          <p style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>
            他の画面に移動しても処理は継続されます
          </p>
        </>
      ) : (
        <p className={styles.summaryText}>{summary}</p>
      )}
    </div>
  );
}
