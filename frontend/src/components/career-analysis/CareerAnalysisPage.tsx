import { useState } from "react";
import {
  type CareerAnalysisResponse,
  type CareerAnalysisResult,
  type EvidenceSource,
} from "../../api";
import { useCareerAnalysisPage } from "../../hooks/useCareerAnalysisPage";
import { ErrorToast } from "../ui/ErrorToast";
import { InlineSpinner } from "../ui/InlineSpinner";
import styles from "./CareerAnalysisPage.module.css";

/**
 * AI キャリアパス分析ページ。
 * 分析生成・履歴管理・結果表示を1画面で行う。
 */
export function CareerAnalysisPage() {
  const { phase, setPhase, error, analyses, handleGenerate, handleDelete } =
    useCareerAnalysisPage();
  const [selected, setSelected] = useState<CareerAnalysisResponse | null>(null);
  const [targetPosition, setTargetPosition] = useState("");

  const handleSelect = (a: CareerAnalysisResponse) => {
    setSelected(a);
    setPhase("detail");
  };

  const handleDeleteWithSelected = async (id: number) => {
    const updated = await handleDelete(id);
    if (updated !== null && selected?.id === id) {
      setSelected(null);
      setPhase(updated.length > 0 ? "list" : "input");
    }
  };

  // ── レンダリング ──────────────────────────────────────────

  if (phase === "loading") {
    return <InlineSpinner label="読み込み中..." />;
  }

  if (phase === "polling") {
    return (
      <InlineSpinner
        label="AI がキャリアを分析中です..."
        sublabel="他の画面に移動しても処理は継続されます"
      />
    );
  }

  // ── 入力 + 履歴 ────────────────────────────────────────

  if (phase === "input" || phase === "list") {
    return (
      <div className={styles.dashboard}>
        <div className={styles.inputCard}>
          <h2>AI キャリアパス分析</h2>
          <p>ターゲットポジションを入力して、AI によるキャリアパス提案を受け取ります。</p>
          <div>
            <input
              type="text"
              placeholder="例: SRE / Platform Engineering / Backend"
              value={targetPosition}
              onChange={(e) => setTargetPosition(e.target.value)}
              style={{ width: "100%", marginBottom: "1rem" }}
            />
          </div>
          <button
            className={styles.generateButton}
            onClick={() => handleGenerate(targetPosition)}
            disabled={!targetPosition.trim()}
          >
            分析を開始
          </button>
          {error && (
            <ErrorToast
              code={error.code}
              message={error.message}
              action={error.action}
              errorId={error.errorId}
              onRetry={targetPosition.trim() ? () => handleGenerate(targetPosition) : undefined}
            />
          )}
        </div>

        {analyses.length > 0 && (
          <div className={styles.section}>
            <h2>分析履歴</h2>
            <div className={styles.versionList}>
              {analyses.map((a) => (
                <div key={a.id} className={styles.versionItem}>
                  <div className={styles.versionMeta}>
                    <span className={styles.versionBadge}>v{a.version}</span>
                    <span className={styles.versionPosition}>{a.target_position}</span>
                    <span className={styles.versionDate}>
                      {new Date(a.created_at).toLocaleDateString("ja-JP")}
                    </span>
                    {a.status === "failed" && (
                      <span style={{ color: "var(--error)", fontSize: "0.8rem" }}>失敗</span>
                    )}
                  </div>
                  <div className={styles.versionActions}>
                    {a.status === "completed" && a.result && (
                      <button onClick={() => handleSelect(a)}>表示</button>
                    )}
                    <button className={styles.deleteButton} onClick={() => handleDeleteWithSelected(a.id)}>
                      削除
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  }

  // ── 分析結果表示 ────────────────────────────────────────

  if (phase === "detail" && selected?.result) {
    const r = selected.result;
    return (
      <div className={styles.dashboard}>
        <div className={styles.dashboardHeader}>
          <h1>
            v{selected.version} — {selected.target_position}
          </h1>
          <button className={styles.backButton} onClick={() => setPhase("list")}>
            一覧に戻る
          </button>
        </div>

        <GrowthSummarySection result={r} />
        <TechStackSection result={r} />
        <StrengthsSection result={r} />
        <CareerPathsSection result={r} />
        <ActionItemsSection result={r} />
      </div>
    );
  }

  return null;
}

/* ── サブコンポーネント ─────────────────────────────────── */

function GrowthSummarySection({ result }: { result: CareerAnalysisResult }) {
  return (
    <div className={styles.resultCard}>
      <div className={styles.resultHeader}>成長曲線</div>
      <div className={styles.resultBody}>{result.growth_summary}</div>
    </div>
  );
}

function TechStackSection({ result }: { result: CareerAnalysisResult }) {
  const grouped = {
    1: result.tech_stack.top.filter((t) => t.priority === 1),
    2: result.tech_stack.top.filter((t) => t.priority === 2),
    3: result.tech_stack.top.filter((t) => t.priority === 3),
  };
  const labels = { 1: "案件実績", 2: "個人開発", 3: "資格" } as const;
  const stars = { 1: "★★★", 2: "★★☆", 3: "★☆☆" } as const;
  const priorityStyle = {
    1: styles.priority1,
    2: styles.priority2,
    3: styles.priority3,
  } as const;

  return (
    <div className={styles.resultCard}>
      <div className={styles.resultHeader}>技術スタック評価</div>
      <div className={styles.resultBody}>
        {([1, 2, 3] as const).map(
          (p) =>
            grouped[p].length > 0 && (
              <div key={p} className={styles.techGroup}>
                <div className={`${styles.techGroupLabel} ${priorityStyle[p]}`}>
                  {stars[p]} {labels[p]}
                </div>
                <div className={styles.techChips}>
                  {grouped[p].map((t) => (
                    <span key={t.name} className={styles.techChip} title={t.note || ""}>
                      {t.name}
                    </span>
                  ))}
                </div>
              </div>
            ),
        )}
        {result.tech_stack.summary && (
          <div className={styles.techSummary}>{result.tech_stack.summary}</div>
        )}
      </div>
    </div>
  );
}

const BADGE_MAP: Record<EvidenceSource, { label: string; className: string }> = {
  resume: { label: "本業", className: styles.badgeResume },
  github: { label: "GitHub", className: styles.badgeGithub },
  blog: { label: "ブログ", className: styles.badgeBlog },
};

function StrengthsSection({ result }: { result: CareerAnalysisResult }) {
  return (
    <div className={styles.resultCard}>
      <div className={styles.resultHeader}>強み（根拠付き）</div>
      <div className={styles.resultBody}>
        {result.strengths.map((s, i) => {
          const badge = BADGE_MAP[s.evidence_source] || BADGE_MAP.resume;
          return (
            <div key={i} className={styles.strengthItem}>
              <div className={styles.strengthTitle}>
                <span className={`${styles.badge} ${badge.className}`}>{badge.label}</span>
                {s.title}
              </div>
              <div className={styles.strengthDetail}>{s.detail}</div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function CareerPathsSection({ result }: { result: CareerAnalysisResult }) {
  return (
    <div className={styles.resultCard}>
      <div className={styles.resultHeader}>キャリアパス提案</div>
      {result.career_paths.map((cp) => (
        <div key={cp.horizon} className={styles.careerPath}>
          <div className={styles.pathHead}>
            <span className={styles.pathTitle}>{cp.title}</span>
            <span className={styles.pathLabel}>{cp.label}</span>
          </div>
          <div className={styles.fitScore}>
            <span>フィットスコア {cp.fit_score}</span>
            <div className={styles.progressBar}>
              <div className={styles.progressFill} style={{ width: `${cp.fit_score}%` }} />
            </div>
          </div>
          <div className={styles.pathDescription}>{cp.description}</div>
          {cp.required_skills.length > 0 && (
            <div className={styles.skillTags}>
              <span style={{ fontSize: "0.78rem", color: "var(--text-muted)" }}>必要スキル:</span>
              {cp.required_skills.map((sk) => (
                <span key={sk} className={styles.skillTag}>
                  {sk}
                </span>
              ))}
            </div>
          )}
          {cp.gap_skills.length > 0 && (
            <div className={styles.skillTags}>
              <span style={{ fontSize: "0.78rem", color: "var(--text-muted)" }}>ギャップ:</span>
              {cp.gap_skills.map((sk) => (
                <span key={sk} className={styles.gapTag}>
                  {sk}
                </span>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

function ActionItemsSection({ result }: { result: CareerAnalysisResult }) {
  return (
    <div className={styles.resultCard}>
      <div className={styles.resultHeader}>アクションアイテム</div>
      <div className={styles.resultBody}>
        {result.action_items.map((a, i) => (
          <div key={i} className={styles.actionItem}>
            <div>
              <span className={styles.actionPriority}>{a.priority}</span>
              <span className={styles.actionText}>{a.action}</span>
            </div>
            <div className={styles.actionReason}>{a.reason}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
