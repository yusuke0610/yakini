import type { TaskProgress } from "../api/intelligence";
import styles from "./TaskProgressStepper.module.css";

type Props = {
  progress: TaskProgress | null;
};

/**
 * GitHub 分析タスクのステップ進捗を表示するコンポーネント。
 * - progress が null（Redis 障害等）のときはスピナーのみ表示（graceful degradation）
 * - step_index === total_steps のとき完了スタイルに切り替え
 */
export function TaskProgressStepper({ progress }: Props) {
  // Redis 障害等で進捗が取れない場合はスピナーのみ（既存 UI と同等）
  if (progress === null || progress.step_index === 0) {
    return (
      <div className={styles.container}>
        <div className={styles.spinner} />
        <p className={styles.label}>GitHubプロフィールを分析中...</p>
        <p className={styles.hint}>他の画面に移動しても処理は継続されます</p>
      </div>
    );
  }

  const { step_index, total_steps, step_label, sub_progress } = progress;
  const isDone = step_index >= total_steps;
  const progressPct = Math.round((step_index / total_steps) * 100);

  return (
    <div className={styles.container}>
      {/* ステップバー */}
      <div className={styles.barTrack} role="progressbar" aria-valuenow={progressPct} aria-valuemin={0} aria-valuemax={100}>
        <div
          className={`${styles.barFill} ${isDone ? styles.barFillDone : ""}`}
          style={{ width: `${progressPct}%` }}
        />
      </div>

      {/* ステップカウンタ */}
      <p className={`${styles.counter} ${isDone ? styles.counterDone : ""}`}>
        {step_index} / {total_steps}
      </p>

      {/* ステップラベル */}
      {step_label && (
        <p className={`${styles.label} ${isDone ? styles.labelDone : ""}`}>
          {step_label}
        </p>
      )}

      {/* リポジトリ詳細取得中の細粒度進捗 */}
      {sub_progress && (
        <p className={styles.subProgress}>
          リポジトリ {sub_progress.done} / {sub_progress.total}
        </p>
      )}

      {!isDone && <p className={styles.hint}>他の画面に移動しても処理は継続されます</p>}
    </div>
  );
}
