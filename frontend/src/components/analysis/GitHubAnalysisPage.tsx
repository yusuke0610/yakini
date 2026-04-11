import { useState } from "react";
import {
  analyzeGitHub,
  getAnalysisCache,
  getAnalysisCacheStatus,
  toAppError,
  type AnalysisResponse,
} from "../../api";
import { ErrorToast } from "../ui/ErrorToast";
import { useAsyncAnalysisPage } from "../../hooks/analysis/useAsyncAnalysisPage";
import { LanguageBar } from "./LanguageBar";
import { PositionRadarChart } from "./PositionRadarChart";
import shared from "../../styles/shared.module.css";
import styles from "./GitHubAnalysisPage.module.css";

/**
 * GitHub 分析結果を表示するダッシュボードコンポーネント。
 * 初回表示時にDBキャッシュを読み込み、保存済みの結果があればそのまま表示する。
 * 「再分析」ボタン押下時のみパイプラインを再実行する。
 */
export function GitHubAnalysisPage() {
  const [includeForks, setIncludeForks] = useState(false);
  /** ポジションアドバイス（GitHub 固有のキャッシュデータ） */
  const [positionAdvice, setPositionAdvice] = useState<string | null>(null);

  const {
    phase,
    result,
    setResult,
    error,
    setError,
    transitionToPolling,
    backToInput,
  } = useAsyncAnalysisPage<AnalysisResponse>({
    loadCache: async () => {
      const cache = await getAnalysisCache();
      // ポジションアドバイスをページ固有の状態として保持する
      if (cache.position_advice) {
        setPositionAdvice(cache.position_advice);
      }
      return { result: cache.analysis_result, status: cache.status };
    },
    checkStatus: getAnalysisCacheStatus,
  });

  /**
   * GitHub 分析を開始します（非同期バックグラウンド）。
   */
  const handleAnalyze = async () => {
    setError(null);
    setPositionAdvice(null);
    try {
      await analyzeGitHub({ include_forks: includeForks });
      transitionToPolling();
    } catch (e) {
      setError(toAppError(e, "分析に失敗しました"));
    }
  };

  /**
   * 入力画面に戻ります（再分析用）。
   */
  const handleBack = () => {
    setPositionAdvice(null);
    setResult(null);
    backToInput();
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


          <button
            type="button"
            className={styles.analyzeButton}
            onClick={handleAnalyze}
          >
            分析開始
          </button>

          {error && (
            <ErrorToast
              code={error.code}
              message={error.message}
              action={error.action}
              errorId={error.errorId}
              onRetry={handleAnalyze}
            />
          )}
        </div>
      </div>
    );
  }

  // ── フェーズ: ポーリング中 ────────────────────────────────────────
  if (phase === "polling") {
    return (
      <div className={shared.pageBody}>
        <div className={styles.loading}>
          <div className={styles.spinner} />
          <p>GitHubプロフィールを分析中...</p>
          <p style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>
            他の画面に移動しても処理は継続されます
          </p>
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

        {error && (
          <ErrorToast
            code={error.code}
            message={error.message}
            action={error.action}
            errorId={error.errorId}
            onRetry={handleAnalyze}
          />
        )}

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
