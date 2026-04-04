import type { ResumeHistory } from "../../../types";
import shared from "../../../styles/shared.module.css";

/** ResumeEducationSection のプロパティ型 */
type ResumeEducationSectionProps = {
  /** 学歴データの配列 */
  educations: ResumeHistory[];
  /** フィールド変更コールバック */
  onFieldChange: (index: number, key: keyof ResumeHistory, value: string) => void;
  /** 学歴追加コールバック */
  onAdd: () => void;
  /** 学歴削除コールバック */
  onRemove: (index: number) => void;
};

/**
 * 履歴書の学歴セクション。
 * 学歴のフィールド群と追加・削除操作を担う。
 */
export function ResumeEducationSection({
  educations,
  onFieldChange,
  onAdd,
  onRemove,
}: ResumeEducationSectionProps) {
  return (
    <section className={shared.section}>
      <h2>学歴</h2>
      {educations.map((education, index) => (
        <div key={`education-${index}`} className={shared.entry}>
          <div className={shared.inline}>
            <label>
              日付
              <input
                type="month"
                value={education.date}
                onChange={(e) => onFieldChange(index, "date", e.target.value)}
              />
            </label>
            <label>
              名称
              <input
                type="text"
                value={education.name}
                onChange={(e) => onFieldChange(index, "name", e.target.value)}
              />
            </label>
          </div>
          <button type="button" className="danger" onClick={() => onRemove(index)}>
            学歴を削除
          </button>
        </div>
      ))}
      <button type="button" className="ghost" onClick={onAdd}>
        学歴を追加
      </button>
    </section>
  );
}

