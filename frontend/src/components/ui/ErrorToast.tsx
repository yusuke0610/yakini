import { ERROR_CONFIG } from "../../constants/errorMessages";
import styles from "./ErrorToast.module.css";

type Props = {
  code: string;
  message?: string;
  action?: string | null;
  onRetry?: () => void;
  errorId?: string;
};

export function ErrorToast({ code, message, action, onRetry, errorId }: Props) {
  const config = ERROR_CONFIG[code] ?? ERROR_CONFIG.INTERNAL_ERROR;
  const recovery = config.recovery;
  const recoveryFn = onRetry ?? recovery?.fn;
  const resolvedMessage = message ?? config.message;

  return (
    <div className={styles.root} role="alert">
      <p className={styles.message}>{resolvedMessage}</p>
      {(recovery || action) && (
        <div className={styles.actions}>
          {recovery && (
            <button
              type="button"
              className={styles.actionButton}
              onClick={recoveryFn ?? undefined}
              disabled={!recoveryFn}
            >
              {recovery.label}
            </button>
          )}
          {action && <p className={styles.actionText}>{action}</p>}
        </div>
      )}
      {errorId && <p className={styles.errorId}>エラーID: {errorId}</p>}
    </div>
  );
}
