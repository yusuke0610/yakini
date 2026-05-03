import styles from "./ConfirmDialog.module.css";

export function ConfirmDialog({
  message,
  confirmLabel,
  confirmingLabel,
  onConfirm,
  onCancel,
  confirming,
}: {
  message: string;
  confirmLabel: string;
  confirmingLabel?: string;
  onConfirm: () => void;
  onCancel: () => void;
  confirming?: boolean;
}) {
  return (
    <div className={styles.overlay} onClick={onCancel}>
      <div className={styles.dialog} onClick={(e) => e.stopPropagation()}>
        <p className={styles.message}>{message}</p>
        <div className={styles.actions}>
          <button type="button" className="danger" onClick={onConfirm} disabled={confirming}>
            {confirming ? (confirmingLabel ?? "削除中...") : confirmLabel}
          </button>
          <button type="button" onClick={onCancel} disabled={confirming}>
            キャンセル
          </button>
        </div>
      </div>
    </div>
  );
}
