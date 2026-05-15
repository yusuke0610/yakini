import {
  type CareerAnalysisResponse,
  type CareerAnalysisResult,
  type EvidenceSource,
} from "../../../api";
import styles from "../CareerAnalysisPage.module.css";

/** スキル名 → 公式ドキュメント URL のキュレーション済みマップ */
const OFFICIAL_DOCS: Record<string, string> = {
  TypeScript: "https://www.typescriptlang.org/docs/",
  Python: "https://docs.python.org/ja/3/",
  Go: "https://go.dev/doc/",
  Rust: "https://doc.rust-lang.org/book/",
  Java: "https://docs.oracle.com/javase/",
  "C#": "https://learn.microsoft.com/ja-jp/dotnet/csharp/",
  Kotlin: "https://kotlinlang.org/docs/",
  Swift: "https://docs.swift.org/swift-book/",
  React: "https://react.dev/learn",
  "Next.js": "https://nextjs.org/docs",
  Vue: "https://ja.vuejs.org/guide/",
  Angular: "https://angular.jp/docs",
  FastAPI: "https://fastapi.tiangolo.com/ja/",
  Django: "https://docs.djangoproject.com/ja/",
  "Spring Boot": "https://spring.io/guides",
  "Node.js": "https://nodejs.org/ja/docs/",
  Docker: "https://docs.docker.com/",
  Kubernetes: "https://kubernetes.io/ja/docs/",
  Terraform: "https://developer.hashicorp.com/terraform/docs",
  "GitHub Actions": "https://docs.github.com/ja/actions",
  AWS: "https://docs.aws.amazon.com/",
  GCP: "https://cloud.google.com/docs?hl=ja",
  Azure: "https://learn.microsoft.com/ja-jp/azure/",
  PostgreSQL: "https://www.postgresql.org/docs/",
  MySQL: "https://dev.mysql.com/doc/",
  Redis: "https://redis.io/docs/",
  MongoDB: "https://www.mongodb.com/docs/",
};

type CareerAnalysisResultViewProps = {
  selected: CareerAnalysisResponse;
  onBack: () => void;
};

/** 分析結果詳細ビュー。全結果セクションをまとめて表示する。 */
export function CareerAnalysisResultView({ selected, onBack }: CareerAnalysisResultViewProps) {
  if (!selected.result) return null;
  const r = selected.result;
  return (
    <div className={styles.dashboard}>
      <div className={styles.dashboardHeader}>
        <h1>
          v{selected.version} — {selected.target_position}
        </h1>
        <button className={styles.backButton} onClick={onBack}>
          一覧に戻る
        </button>
      </div>

      <GrowthSummarySection result={r} />
      <TechStackSection result={r} />
      <StrengthsSection result={r} />
      <CareerPathsSection result={r} />
      <ActionItemsSection result={r} />
      <LearningResourcesSection result={r} />
    </div>
  );
}

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

function LearningResourcesSection({ result }: { result: CareerAnalysisResult }) {
  const gapSkills = [...new Set(result.career_paths.flatMap((cp) => cp.gap_skills))];
  if (gapSkills.length === 0) return null;

  return (
    <div className={styles.resultCard}>
      <div className={styles.resultHeader}>学習リソース</div>
      <div className={styles.resultBody}>
        <p className={styles.resourceDescription}>
          キャリアパス実現に向けて習得が推奨されるスキルの学習リソースです。
        </p>
        <div className={styles.resourceList}>
          {gapSkills.map((skill) => {
            const officialUrl = OFFICIAL_DOCS[skill];
            const udemyUrl = `https://www.udemy.com/courses/search/?q=${encodeURIComponent(skill)}&lang=ja`;
            return (
              <div key={skill} className={styles.resourceItem}>
                <span className={styles.resourceSkill}>{skill}</span>
                <div className={styles.resourceLinks}>
                  {officialUrl && (
                    <a
                      href={officialUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className={styles.resourceLink}
                    >
                      公式ドキュメント
                    </a>
                  )}
                  <a
                    href={udemyUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className={styles.resourceLink}
                  >
                    Udemy で検索
                  </a>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
