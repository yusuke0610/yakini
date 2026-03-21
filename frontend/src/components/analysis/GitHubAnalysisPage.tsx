import { useState, useEffect } from "react";
import {
  analyzeGitHub,
  getAnalysisCache,
  summarizeAnalysis,
  type AnalysisResponse,
} from "../../api";
import { SkillTimelineChart } from "../SkillTimelineChart";
import { LanguageBar } from "./LanguageBar";
import shared from "../../styles/shared.module.css";
import styles from "./GitHubAnalysisPage.module.css";

type Phase = "loading-cache" | "input" | "loading" | "result";

/**
 * GitHub 分析結果を表示するダッシュボードコンポーネント。
 * 初回表示時にDBキャッシュを読み込み、保存済みの結果があればそのまま表示する。
 * 「再分析」ボタン押下時のみ LLM を再起動する。
 */
export function GitHubAnalysisPage() {
  const [phase, setPhase] = useState<Phase>("loading-cache");
  const [includeForks, setIncludeForks] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AnalysisResponse | null>(null);

  // AI 要約
  const [summary, setSummary] = useState<string | null>(null);
  const [summaryLoading, setSummaryLoading] = useState(false);

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
          setSummary(cache.ai_summary ?? null);
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
    setSummary(null);
    try {
      const data = await analyzeGitHub({
        include_forks: includeForks,
      });
      setResult(data);
      setSummaryLoading(true);
      setPhase("result");
    } catch (e) {
      setError(e instanceof Error ? e.message : "分析に失敗しました");
      setPhase("input");
    }
  };

  /**
   * 再分析後、AI 要約がまだない場合に取得する。
   */
  useEffect(() => {
    if (!result || summary) return;
    if (!summaryLoading) return;
    let cancelled = false;
    summarizeAnalysis(result)
      .then((res) => {
        if (!cancelled && res.available) {
          setSummary(res.summary);
        }
      })
      .catch(() => {})
      .finally(() => {
        if (!cancelled) setSummaryLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [result, summary, summaryLoading]);

  /**
   * 入力画面に戻ります（再分析用）。
   */
  const handleBack = () => {
    setPhase("input");
    setResult(null);
    setSummary(null);
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

        {/* AI 要約 */}
        {(summaryLoading || summary) && (
          <div className={styles.section}>
            <h2>AI要約</h2>
            {summaryLoading ? (
              <p className={styles.summaryLoading}>要約を生成中...</p>
            ) : (
              <p className={styles.summaryText}>{summary}</p>
            )}
          </div>
        )}

        {/* スキル成熟度グラフ */}
        <div className={styles.section}>
          <SkillTimelineChart />
        </div>
      </div>
    </div>
  );
}
