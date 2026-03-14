import { useState, useEffect } from "react";
import {
  analyzeGitHub,
  summarizeAnalysis,
  downloadAnalysisPdf,
  downloadAnalysisMarkdown,
  type AnalysisResponse,
} from "../../api";
import { SkillTimelineChart } from "../SkillTimelineChart";
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
  const [summary, setSummary] = useState<string | null>(
    () => sessionStorage.getItem(CACHE_KEY_SUMMARY),
  );
  const [summaryLoading, setSummaryLoading] = useState(false);

  // ダウンロード状態
  const [downloading, setDownloading] = useState(false);

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
    setSummaryLoading(true);
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

  /**
   * PDF レポートをダウンロードします。
   */
  const handleDownloadPdf = async () => {
    if (!result) return;
    setDownloading(true);
    try {
      await downloadAnalysisPdf(result, summary);
    } catch (e) {
      setError(e instanceof Error ? e.message : "PDFダウンロードに失敗しました");
    } finally {
      setDownloading(false);
    }
  };

  /**
   * Markdown レポートをダウンロードします。
   */
  const handleDownloadMarkdown = async () => {
    if (!result) return;
    setDownloading(true);
    try {
      await downloadAnalysisMarkdown(result, summary);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Markdownダウンロードに失敗しました");
    } finally {
      setDownloading(false);
    }
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

  const { prediction, simulation, growth, year_snapshots } = result;

  // タイムライン行のためにすべてのスナップショットからユニークなスキルを収集
  const allSkills = Array.from(
    new Set(year_snapshots.flatMap((s) => s.skills)),
  );
  const years = year_snapshots.map((s) => s.year);
  const newSkillsByYear = new Map(
    year_snapshots.map((s) => [s.year, new Set(s.new_skills)]),
  );
  const skillsByYear = new Map(
    year_snapshots.map((s) => [s.year, new Set(s.skills)]),
  );

  // 成長トレンドのカテゴリ分け
  const emerging = growth.filter(
    (g) => g.trend === "emerging" || g.trend === "new",
  );
  const stable = growth.filter((g) => g.trend === "stable");
  const declining = growth.filter((g) => g.trend === "declining");

  return (
    <div className={shared.pageBody}>
      <div className={styles.dashboard}>
        {/* ヘッダー */}
        <div className={styles.dashboardHeader}>
          <h1>{result.username} の分析結果</h1>
          <div className={styles.headerActions}>
            <button
              type="button"
              className={styles.downloadButton}
              onClick={handleDownloadPdf}
              disabled={downloading}
            >
              PDF
            </button>
            <button
              type="button"
              className={styles.downloadButton}
              onClick={handleDownloadMarkdown}
              disabled={downloading}
            >
              Markdown
            </button>
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
            <div className={styles.statCard}>
              <div className={styles.statValue}>
                {prediction.current_role.role_name}
              </div>
              <div className={styles.statLabel}>
                現在のロール ({(prediction.current_role.confidence * 100).toFixed(0)}%)
              </div>
            </div>
          </div>
        </div>

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

        {/* スキルタイムライン */}
        {year_snapshots.length > 0 && (
          <div className={styles.section}>
            <h2>スキルタイムライン</h2>
            <div className={styles.timelineGrid}>
              {/* ヘッダー行 */}
              <div className={`${styles.timelineRow} ${styles.timelineHeaderRow}`}>
                <div className={styles.timelineSkillCell} />
                {years.map((y) => (
                  <div key={y} className={styles.timelineCell}>
                    {y}
                  </div>
                ))}
              </div>
              {/* スキル行 */}
              {allSkills.map((skill) => (
                <div key={skill} className={styles.timelineRow}>
                  <div className={styles.timelineSkillCell}>{skill}</div>
                  {years.map((y) => {
                    const hasSkill = skillsByYear.get(y)?.has(skill);
                    const isNew = newSkillsByYear.get(y)?.has(skill);
                    return (
                      <div key={y} className={styles.timelineCell}>
                        {hasSkill ? (
                          <span
                            className={`${styles.timelineDot} ${isNew ? styles.timelineDotNew : ""}`}
                          />
                        ) : (
                          <span className={styles.timelineEmpty} />
                        )}
                      </div>
                    );
                  })}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 成長トレンド */}
        {growth.length > 0 && (
          <div className={styles.section}>
            <h2>スキル成長トレンド</h2>
            <div className={styles.growthGrid}>
              <div className={`${styles.growthColumn} ${styles.growthEmerging}`}>
                <h3>Emerging / New</h3>
                {emerging.map((g) => (
                  <div key={g.skill_name} className={styles.growthItem}>
                    <span
                      className={`${styles.growthBadge} ${g.trend === "new" ? styles.badgeNew : styles.badgeEmerging}`}
                    >
                      {g.skill_name}
                    </span>
                    <span className={styles.velocity}>
                      {g.velocity > 0 ? "+" : ""}
                      {g.velocity.toFixed(1)}
                    </span>
                  </div>
                ))}
                {emerging.length === 0 && (
                  <span className={styles.velocity}>-</span>
                )}
              </div>
              <div className={`${styles.growthColumn} ${styles.growthStable}`}>
                <h3>Stable</h3>
                {stable.map((g) => (
                  <div key={g.skill_name} className={styles.growthItem}>
                    <span className={`${styles.growthBadge} ${styles.badgeStable}`}>
                      {g.skill_name}
                    </span>
                    <span className={styles.velocity}>
                      {g.velocity.toFixed(1)}
                    </span>
                  </div>
                ))}
                {stable.length === 0 && (
                  <span className={styles.velocity}>-</span>
                )}
              </div>
              <div className={`${styles.growthColumn} ${styles.growthDeclining}`}>
                <h3>Declining</h3>
                {declining.map((g) => (
                  <div key={g.skill_name} className={styles.growthItem}>
                    <span className={`${styles.growthBadge} ${styles.badgeDeclining}`}>
                      {g.skill_name}
                    </span>
                    <span className={styles.velocity}>
                      {g.velocity.toFixed(1)}
                    </span>
                  </div>
                ))}
                {declining.length === 0 && (
                  <span className={styles.velocity}>-</span>
                )}
              </div>
            </div>
          </div>
        )}

        {/* キャリア予測 */}
        <div className={styles.section}>
          <h2>キャリア予測</h2>
          <div className={styles.currentRole}>
            <div className={styles.roleName}>
              {prediction.current_role.role_name}
            </div>
            <div className={styles.confidenceBar}>
              <div
                className={styles.confidenceFill}
                style={{
                  width: `${prediction.current_role.confidence * 100}%`,
                }}
              />
            </div>
            <div className={styles.confidenceLabel}>
              確信度: {(prediction.current_role.confidence * 100).toFixed(0)}%
            </div>
          </div>

          {prediction.next_roles.length > 0 && (
            <>
              <div className={styles.roleSubheading}>次のキャリアステップ</div>
              <div className={styles.roleCards}>
                {prediction.next_roles.map((role) => (
                  <div key={role.role_name} className={styles.roleCard}>
                    <div className={styles.roleName}>{role.role_name}</div>
                    <div className={styles.confidenceBar}>
                      <div
                        className={styles.confidenceFill}
                        style={{ width: `${role.confidence * 100}%` }}
                      />
                    </div>
                    <div className={styles.confidenceLabel}>
                      {(role.confidence * 100).toFixed(0)}%
                    </div>
                    {role.missing_skills.length > 0 && (
                      <div className={styles.missingSkills}>
                        {role.missing_skills.map((s) => (
                          <span key={s} className={styles.missingTag}>
                            {s}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </>
          )}

          {prediction.long_term_roles.length > 0 && (
            <>
              <div className={styles.roleSubheading}>長期キャリア候補</div>
              <div className={styles.roleCards}>
                {prediction.long_term_roles.map((role) => (
                  <div key={role.role_name} className={styles.roleCard}>
                    <div className={styles.roleName}>{role.role_name}</div>
                    <div className={styles.confidenceLabel}>
                      {(role.confidence * 100).toFixed(0)}%
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>

        {/* キャリアパスシミュレーション */}
        {simulation.paths.length > 0 && (
          <div className={styles.section}>
            <h2>キャリアパスシミュレーション</h2>
            <div className={styles.pathList}>
              {simulation.paths.map((p, i) => (
                <div key={i} className={styles.pathItem}>
                  <div className={styles.pathFlow}>
                    {p.path.map((role, j) => (
                      <span key={j}>
                        <span className={styles.pathRole}>{role}</span>
                        {j < p.path.length - 1 && (
                          <span className={styles.pathArrow}> → </span>
                        )}
                      </span>
                    ))}
                  </div>
                  <div className={styles.pathConfidence}>
                    確信度: {(p.confidence * 100).toFixed(0)}%
                  </div>
                  {p.description && (
                    <div className={styles.pathDescription}>{p.description}</div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
