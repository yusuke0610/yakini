import { useMemo, useState } from "react";
import { marked } from "marked";
import shared from "../../styles/shared.module.css";
import styles from "./MarkdownTextarea.module.css";

type Mode = "text" | "markdown";

type Props = {
  /** フィールドのラベル */
  label: string;
  /** テキストの値 */
  value: string;
  /** 値変更コールバック */
  onChange: (value: string) => void;
  /** textarea の行数（デフォルト: 3） */
  rows?: number;
  /** placeholder */
  placeholder?: string;
  /** 必須フィールドかどうか */
  required?: boolean;
};

/**
 * ノーマルテキスト / Markdown を切り替えられるテキストエリア。
 * Markdown モードでは「編集」と「プレビュー」タブを表示する。
 */
export function MarkdownTextarea({ label, value, onChange, rows = 3, placeholder, required }: Props) {
  const [mode, setMode] = useState<Mode>("text");
  const [tab, setTab] = useState<"edit" | "preview">("edit");

  /** marked で HTML を生成（XSS 対策: marked のデフォルト sanitizer を利用） */
  const renderedHtml = useMemo(() => {
    if (mode !== "markdown" || tab !== "preview") return "";
    return marked.parse(value || "", { async: false }) as string;
  }, [mode, tab, value]);

  return (
    <div className={styles.wrapper}>
      <div className={styles.toolbar}>
        <span className={shared.labelText}>
          {label}
          {required && <span className={shared.requiredBadge}>必須</span>}
        </span>
        <div className={styles.modeToggle}>
          <button
            type="button"
            className={mode === "text" ? styles.active : ""}
            onClick={() => { setMode("text"); setTab("edit"); }}
          >
            テキスト
          </button>
          <button
            type="button"
            className={mode === "markdown" ? styles.active : ""}
            onClick={() => setMode("markdown")}
          >
            Markdown
          </button>
        </div>
        {mode === "markdown" && (
          <div className={styles.modeToggle}>
            <button
              type="button"
              className={tab === "edit" ? styles.active : ""}
              onClick={() => setTab("edit")}
            >
              編集
            </button>
            <button
              type="button"
              className={tab === "preview" ? styles.active : ""}
              onClick={() => setTab("preview")}
            >
              プレビュー
            </button>
          </div>
        )}
      </div>

      {tab === "edit" ? (
        <textarea
          rows={rows}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          required={required}
        />
      ) : (
        <div
          className={styles.preview}
          style={{ minHeight: `${rows * 1.5}rem` }}
          dangerouslySetInnerHTML={{ __html: renderedHtml }}
        />
      )}
    </div>
  );
}
