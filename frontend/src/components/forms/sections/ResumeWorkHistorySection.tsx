import type { ResumeHistory } from "../../../types";
import shared from "../../../styles/shared.module.css";

/** ResumeWorkHistorySection のプロパティ型 */
type ResumeWorkHistorySectionProps = {
  /** 職歴データの配列 */
  workHistories: ResumeHistory[];
  /** フィールド変更コールバック */
  onFieldChange: (index: number, key: keyof ResumeHistory, value: string) => void;
  /** 職歴追加コールバック */
  onAdd: () => void;
  /** 職歴削除コールバック */
  onRemove: (index: number) => void;
};

/**
 * 履歴書の職歴セクション。
 * 職歴のフィールド群と追加・削除操作を担う。
 */
export function ResumeWorkHistorySection({
  workHistories,
  onFieldChange,
  onAdd,
  onRemove,
}: ResumeWorkHistorySectionProps) {
  return (
    <section className={shared.section}>
      <h2>職歴</h2>
      {workHistories.map((workHistory, index) => (
        <div key={`work-${index}`} className={shared.entry}>
          <div className={shared.inline}>
            <label>
              日付
              <input
                type="month"
                value={workHistory.date}
                onChange={(e) => onFieldChange(index, "date", e.target.value)}
              />
            </label>
            <label>
              名称
              <input
                type="text"
                value={workHistory.name}
                onChange={(e) => onFieldChange(index, "name", e.target.value)}
              />
            </label>
          </div>
          <button type="button" className="danger" onClick={() => onRemove(index)}>
            職歴を削除
          </button>
        </div>
      ))}
      <button type="button" className="ghost" onClick={onAdd}>
        職歴を追加
      </button>
    </section>
  );
}

