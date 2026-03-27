import { useState, useEffect } from "react";
import { getBlogScore, type BlogScoreResponse } from "../../api/blog";
import styles from "./BlogScoreCard.module.css";

const RANK_COLORS: Record<string, string> = {
  S: "#d4a017",
  A: "#dc3545",
  B: "#0d6efd",
  C: "#198754",
  D: "#6c757d",
  E: "#adb5bd",
};

interface AxisDisplayProps {
  label: string;
  rank: string;
  detail: string;
}

function AxisDisplay({ label, rank, detail }: AxisDisplayProps) {
  return (
    <div className={styles.axisItem}>
      <span className={styles.axisLabel}>{label}</span>
      <span
        className={styles.axisRank}
        style={{ color: RANK_COLORS[rank] || RANK_COLORS.E }}
      >
        {rank}
      </span>
      <span className={styles.axisDetail}>{detail}</span>
    </div>
  );
}

/**
 * ブログスコアリング結果を表示するカードコンポーネント。
 * 総合ランク + 3軸の内訳を表示する。
 */
export function BlogScoreCard() {
  const [score, setScore] = useState<BlogScoreResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    getBlogScore()
      .then((data) => {
        if (!cancelled) setScore(data);
      })
      .catch(() => {})
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) {
    return (
      <div className={styles.card}>
        <p className={styles.loading}>スコアを計算中...</p>
      </div>
    );
  }

  if (!score) return null;

  const overallColor = RANK_COLORS[score.overall_rank] || RANK_COLORS.E;

  return (
    <div className={styles.card}>
      <h3 className={styles.title}>Tech Blog Score</h3>

      {/* 総合ランク */}
      <div className={styles.overallSection}>
        <div
          className={styles.overallRank}
          style={{ color: overallColor, borderColor: overallColor }}
        >
          {score.overall_rank}
        </div>
        <div className={styles.overallMeta}>
          <span>技術記事: {score.tech_article_count} / {score.total_article_count} 件</span>
        </div>
      </div>

      {score.tech_article_count === 0 ? (
        <p className={styles.noArticles}>
          技術記事が見つかりませんでした
        </p>
      ) : (
        <>
          {/* 3軸の内訳 */}
          <div className={styles.axisGrid}>
            <AxisDisplay
              label="投稿頻度"
              rank={score.frequency_rank}
              detail={`月 ${score.avg_monthly_posts} 回`}
            />
            <AxisDisplay
              label="反応"
              rank={score.reaction_rank}
              detail={`平均 ${score.avg_likes} いいね`}
            />
            <AxisDisplay
              label="記事数"
              rank={score.count_rank}
              detail={`${score.tech_article_count} 件`}
            />
          </div>
        </>
      )}
    </div>
  );
}
