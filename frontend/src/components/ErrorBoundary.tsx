import { ErrorBoundary as ReactErrorBoundary } from "react-error-boundary";
import type { ReactNode } from "react";

import { generateErrorId } from "../utils/errorId";
import styles from "./ErrorBoundary.module.css";

type ErrorBoundaryProps = {
  children: ReactNode;
};

type FallbackProps = {
  resetErrorBoundary: () => void;
};

function FallbackComponent({ resetErrorBoundary }: FallbackProps) {
  const errorId = generateErrorId();

  return (
    <div className={styles.root}>
      <div className={styles.card}>
        <p className={styles.eyebrow}>Application Error</p>
        <h1 className={styles.title}>予期しないエラーが発生しました</h1>
        <p className={styles.description}>
          ページの表示中に問題が発生しました。再読み込みするか、ホームへ戻ってください。
        </p>
        <div className={styles.actions}>
          <button
            type="button"
            className={styles.secondaryButton}
            onClick={() => window.location.assign("/career")}
          >
            ホームに戻る
          </button>
          <button type="button" className={styles.primaryButton} onClick={resetErrorBoundary}>
            ページを再読み込み
          </button>
        </div>
        <p className={styles.description}>エラーID: {errorId}</p>
      </div>
    </div>
  );
}

export default function ErrorBoundary({ children }: ErrorBoundaryProps) {
  return (
    <ReactErrorBoundary
      FallbackComponent={FallbackComponent}
      onReset={() => window.location.reload()}
    >
      {children}
    </ReactErrorBoundary>
  );
}
