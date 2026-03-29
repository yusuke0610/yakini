import { useState, useEffect } from "react";
import {
  analyzeGitHub,
  getAnalysisCache,
  type AnalysisResponse,
} from "../../api";
import { LanguageBar } from "./LanguageBar";
import { PositionRadarChart } from "./PositionRadarChart";
import shared from "../../styles/shared.module.css";
import styles from "./GitHubAnalysisPage.module.css";

type Phase = "loading-cache" | "input" | "loading" | "result";

/**
 * GitHub 分析結果を表示するダッシュボードコンポーネント。
 * 初回表示時にDBキャッシュを読み込み、保存済みの結果があればそのまま表示する。
 * 「再分析」ボタン押下時のみパイプラインを再実行する。
 */
export function GitHubAnalysisPage() {
  const [phase, setPhase] = useState<Phase>("loading-cache");
  const [includeForks, setIncludeForks] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AnalysisResponse | null>(null);

  // ポジションアドバイス（現状分析+学習アドバイス）
  const [positionAdvice, setPositionAdvice] = useState<string | null>(null);

  /**
   * 初回マウント時にDBキャッシュを読み込む。
   */
  useEffect(() => {
    let cancelled = false;
    getAnalysisCache()
      .then((cache) => {
        if (cancelled) return;
        if (cache.analysis_result) {
          setResult(cache.analysis_result);
          setPositionAdvice(cache.position_advice ?? null);
          setPhase("result");
        } else {
          setPhase("input");
        }
      })
      .catch(() => {
        if (!cancelled) setPhase("input");
      });
    return () => { cancelled = true; };
  }, []);

  /**
   * GitHub 分析を実行します（再分析）。
   */
  const handleAnalyze = async () => {
    setError(null);
    setPhase("loading");
    setPositionAdvice(null);
    try {
      const data = await analyzeGitHub({
        include_forks: includeForks,
      });
      setResult(data);
      setPhase("result");
    } catch (e) {
      setError(e instanceof Error ? e.message : "分析に失敗しました");
      setPhase("input");
    }
  };

  /**
   * 入力画面に戻ります（再分析用）。
   */
  const handleBack = () => {
    setPhase("input");
    setResult(null);
    setPositionAdvice(null);
  };

  // ── フェーズ: キャッシュ読み込み中 ──────────────────────────────
  if (phase === "loading-cache") {
    return (
      <div className={shared.pageBody}>
        <div className={styles.loading}>
          <div className={styles.spinner} />
          <p>読み込み中...</p>
        </div>
      </div>
    );
  }

  // ── フェーズ: 入力 ──────────────────────────────────────────
  if (phase === "input") {
    return (
      <div className={shared.pageBody}>
        <div className={styles.inputCard}>
          <h2>GitHub分析</h2>
          <p>あなたのGitHubアクティビティからスキルとキャリアを分析します</p>

          <button
            type="button"
            className={styles.advancedToggle}
            onClick={() => setShowAdvanced(!showAdvanced)}
          >
            {showAdvanced ? "▼" : "▶"} 詳細オプション
          </button>

          {showAdvanced && (
            <div className={styles.advancedOptions}>
              <div className={styles.checkbox}>
                <input
                  type="checkbox"
                  id="includeForks"
                  checked={includeForks}
                  onChange={(e) => setIncludeForks(e.target.checked)}
                />
                <label htmlFor="includeForks">フォークしたリポジトリを含む</label>
              </div>
            </div>
          )}

          <button
            type="button"
            className={styles.analyzeButton}
            onClick={handleAnalyze}
          >
            分析開始
          </button>

          {error && <p className={styles.errorMessage}>{error}</p>}
        </div>
      </div>
    );
  }

  // ── フェーズ: ローディング ────────────────────────────────────────
  if (phase === "loading") {
    return (
      <div className={shared.pageBody}>
        <div className={styles.loading}>
          <div className={styles.spinner} />
          <p>GitHubプロフィールを分析中...</p>
        </div>
      </div>
    );
  }

  // ── フェーズ: 分析結果ダッシュボード ───────────────────────────────
  if (!result) return null;

  return (
    <div className={shared.pageBody}>
      <div className={styles.dashboard}>
        {/* ヘッダー */}
        <div className={styles.dashboardHeader}>
          <h1>{result.username} の分析結果</h1>
          <div className={styles.headerActions}>
            <button type="button" className={styles.backButton} onClick={handleBack}>
              再分析
            </button>
          </div>
        </div>

        {error && <p className={styles.errorMessage}>{error}</p>}

        {/* 概要 */}
        <div className={styles.section}>
          <h2>Overview</h2>
          <div className={styles.overviewCards}>
            <div className={styles.statCard}>
              <div className={styles.statValue}>{result.repos_analyzed}</div>
              <div className={styles.statLabel}>リポジトリ</div>
            </div>
            <div className={styles.statCard}>
              <div className={styles.statValue}>{result.unique_skills}</div>
              <div className={styles.statLabel}>スキル</div>
            </div>
          </div>
        </div>

        {/* 構成 */}
        {result.languages && Object.keys(result.languages).length > 0 && (
          <div className={styles.section}>
            <h2>Languages</h2>
            <LanguageBar languages={result.languages} />
          </div>
        )}

        {/* ポジションスコア */}
        {result.position_scores && (
          <div className={styles.section}>
            <h2>Position Score</h2>
            <PositionRadarChart
              scores={result.position_scores}
              cachedAdvice={positionAdvice}
            />
          </div>
        )}
      </div>
    </div>
  );
}
