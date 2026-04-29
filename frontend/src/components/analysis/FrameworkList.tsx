import styles from "./FrameworkList.module.css";

interface Props {
  /** 検出されたフレームワーク名の配列（Issue #203） */
  frameworks: string[];
}

/**
 * GitHub 分析結果から検出されたフレームワーク／ライブラリをチップ風に一覧表示する。
 * 空配列の場合は何も描画しない（呼び出し側のレイアウト負担を減らす）。
 */
export function FrameworkList({ frameworks }: Props) {
  if (!frameworks || frameworks.length === 0) {
    return null;
  }
  return (
    <ul className={styles.list} aria-label="検出フレームワーク一覧">
      {frameworks.map((name) => (
        <li key={name} className={styles.tag}>
          {name}
        </li>
      ))}
    </ul>
  );
}
