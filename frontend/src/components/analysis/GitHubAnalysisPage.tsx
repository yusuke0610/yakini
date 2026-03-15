import { useState, useEffect } from "react";
import {
  analyzeGitHub,
  summarizeAnalysis,
  type AnalysisResponse,
} from "../../api";
import { SkillTimelineChart } from "../SkillTimelineChart";
import { LanguageBar } from "./LanguageBar";
import shared from "../../styles/shared.module.css";
import styles from "./GitHubAnalysisPage.module.css";

const CACHE_KEY_RESULT = "github_analysis_result";
const CACHE_KEY_SUMMARY = "github_analysis_summary";

type Phase = "input" | "loading" | "result";

/**
 * キャッシュされた分析結果を読み込みます。
 */
function loadCachedResult(): AnalysisResponse | null {
  try {
    const raw = sessionStorage.getItem(CACHE_KEY_RESULT);
    return raw ? (JSON.parse(raw) as AnalysisResponse) : null;
  } catch {
    return null;
  }
}

/**
 * GitHub 分析結果を表示するダッシュボードコンポーネント。
 */
export function GitHubAnalysisPage() {
  const cachedResult = loadCachedResult();
  const [phase, setPhase] = useState<Phase>(cachedResult ? "result" : "input");
  const [includeForks, setIncludeForks] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AnalysisResponse | null>(cachedResult);

  // AI 要約
  const cachedSummary = sessionStorage.getItem(CACHE_KEY_SUMMARY);
  const [summary, setSummary] = useState<string | null>(cachedSummary);
  // 結果があり要約キャッシュがない場合、初期状態でローディングを開始
  const [summaryLoading, setSummaryLoading] = useState(
    () => !!cachedResult && !cachedSummary,
  );

  /**
   * GitHub 分析を実行します。
   */
  const handleAnalyze = async () => {
    setError(null);
    setPhase("loading");
    try {
      const data = await analyzeGitHub({
        include_forks: includeForks,
      });
      setResult(data);
      setSummaryLoading(true);
      sessionStorage.setItem(CACHE_KEY_RESULT, JSON.stringify(data));
      setPhase("result");
    } catch (e) {
      setError(e instanceof Error ? e.message : "分析に失敗しました");
      setPhase("input");
    }
  };

  /**
   * 結果が利用可能になった後、AI 要約を取得します（キャッシュがない場合）。
   */
  useEffect(() => {
    if (!result) return;
    if (summary) return; // キャッシュされた要約がすでにある場合
    let cancelled = false;
    summarizeAnalysis(result)
      .then((res) => {
        if (!cancelled && res.available) {
          setSummary(res.summary);
          sessionStorage.setItem(CACHE_KEY_SUMMARY, res.summary);
        }
      })
      .catch(() => {})
      .finally(() => {
        if (!cancelled) setSummaryLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [result, summary]);

  /**
   * 入力画面に戻ります。
   */
  const handleBack = () => {
    setPhase("input");
    setResult(null);
    setSummary(null);
    sessionStorage.removeItem(CACHE_KEY_RESULT);
    sessionStorage.removeItem(CACHE_KEY_SUMMARY);
  };

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
