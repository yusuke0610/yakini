import { useState } from "react";
import type { CareerAnalysisResponse } from "../../api";
import { useCareerAnalysisPage } from "../../hooks/useCareerAnalysisPage";
import { CareerAnalysisResultView } from "./result/CareerAnalysisResultView";
import { ErrorToast } from "../ui/ErrorToast";
import { InlineSpinner } from "../ui/InlineSpinner";
import styles from "./CareerAnalysisPage.module.css";

/**
 * AI キャリアパス分析ページ。
 * 分析生成・履歴管理・結果表示を1画面で行う。
 */
export function CareerAnalysisPage() {
  const { phase, setPhase, error, analyses, handleGenerate, handleDelete, handleRetry } =
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
                    {a.status === "dead_letter" && (
                      <span style={{ color: "var(--error)", fontSize: "0.8rem" }}>失敗</span>
                    )}
                    {a.status === "retrying" && (
                      <span style={{ color: "var(--warning)", fontSize: "0.8rem" }}>
                        再試行中
                      </span>
                    )}
                  </div>
                  <div className={styles.versionActions}>
                    {a.status === "completed" && a.result && (
                      <button onClick={() => handleSelect(a)}>表示</button>
                    )}
                    {a.status === "dead_letter" && (
                      <button onClick={() => handleRetry(a.id)}>再実行</button>
                    )}
                    <button
                      className={styles.deleteButton}
                      onClick={() => handleDeleteWithSelected(a.id)}
                    >
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

  if (phase === "detail" && selected?.result) {
    return (
      <CareerAnalysisResultView
        selected={selected}
        onBack={() => setPhase("list")}
      />
    );
  }

  return null;
}
