import { useState, useEffect, useMemo } from "react";
import { marked } from "marked";
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import {
  getPositionAdvice,
  type PositionScores,
} from "../../api";
import styles from "./PositionRadarChart.module.css";

interface Props {
  scores: PositionScores;
  cachedAdvice?: string | null;
}

const AXIS_LABELS: Record<string, string> = {
  backend: "Backend",
  frontend: "Frontend",
  fullstack: "Fullstack",
  sre: "SRE",
  cloud: "Cloud",
};

/**
 * 5軸のエンジニアポジションスコアをレーダーチャートで表示し、
 * フルスタックへのギャップ分析とAI現状分析+学習アドバイスを提供するコンポーネント。
 */
export function PositionRadarChart({ scores, cachedAdvice }: Props) {
  const [advice, setAdvice] = useState<string | null>(cachedAdvice ?? null);
  const [adviceLoading, setAdviceLoading] = useState(false);

  const chartData = Object.entries(AXIS_LABELS).map(([key, label]) => ({
    axis: label,
    score: scores[key as keyof PositionScores] as number,
  }));

  const adviceHtml = useMemo(() => {
    if (!advice) return "";
    return marked.parse(advice, { async: false }) as string;
  }, [advice]);

  const handleGetAdvice = async () => {
    setAdviceLoading(true);
    try {
      const res = await getPositionAdvice();
      if (res.available) {
        setAdvice(res.advice);
      }
    } catch {
      // エラー時は何もしない
    } finally {
      setAdviceLoading(false);
    }
  };

  useEffect(() => {
    if (cachedAdvice) {
      setAdvice(cachedAdvice);
    }
  }, [cachedAdvice]);

  return (
    <div className={styles.container}>
      {/* レーダーチャート */}
      <div className={styles.chartWrapper}>
        <ResponsiveContainer width="100%" height={320}>
          <RadarChart data={chartData} cx="50%" cy="50%" outerRadius="75%">
            <PolarGrid stroke="var(--border)" />
            <PolarAngleAxis
              dataKey="axis"
              tick={{ fill: "var(--text-secondary)", fontSize: 13 }}
            />
            <PolarRadiusAxis
              angle={90}
              domain={[0, 100]}
              tick={{ fill: "var(--text-muted)", fontSize: 11 }}
              tickCount={6}
            />
            <Radar
              name="Score"
              dataKey="score"
              stroke="var(--accent)"
              fill="var(--accent)"
              fillOpacity={0.25}
              strokeWidth={2}
            />
            <Tooltip
              contentStyle={{
                background: "var(--bg-card)",
                border: "1px solid var(--border)",
                borderRadius: "6px",
                fontSize: "0.85rem",
              }}
              formatter={(value) => [`${value}/100`, "Score"]}
            />
          </RadarChart>
        </ResponsiveContainer>
      </div>

      {/* スコア一覧 */}
      <div className={styles.scoreList}>
        {chartData.map((d) => (
          <div key={d.axis} className={styles.scoreItem}>
            <span className={styles.scoreLabel}>{d.axis}</span>
            <div className={styles.scoreBarTrack}>
              <div
                className={styles.scoreBarFill}
                style={{ width: `${d.score}%` }}
              />
            </div>
            <span className={styles.scoreValue}>{d.score}</span>
          </div>
        ))}
      </div>

      {/* フルスタックへのギャップ */}
      {scores.missing_skills.length > 0 && (
        <div className={styles.gapSection}>
          <h3 className={styles.gapTitle}>
            Fullstack Engineer Gap
          </h3>
          <div className={styles.missingSkills}>
            {scores.missing_skills.map((skill) => (
              <span key={skill} className={styles.missingTag}>
                {skill}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* AI 現状分析 + 学習アドバイス */}
      <div className={styles.adviceSection}>
        {advice ? (
          <div
            className={styles.adviceContent}
            dangerouslySetInnerHTML={{ __html: adviceHtml }}
          />
        ) : (
          <button
            type="button"
            className={styles.adviceButton}
            onClick={handleGetAdvice}
            disabled={adviceLoading}
          >
            {adviceLoading ? "分析・アドバイス生成中..." : "AI分析 & 学習アドバイスを取得"}
          </button>
        )}
      </div>
    </div>
  );
}
