import { Component, type ErrorInfo, type ReactNode } from "react";

import { generateErrorId } from "../utils/errorId";
import styles from "./ErrorBoundary.module.css";

type Props = { children: ReactNode };
type State = { hasError: boolean };

export default class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false };

  static getDerivedStateFromError(): State {
    return { hasError: true };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("[ErrorBoundary]", error, info.componentStack);
  }

  render() {
    if (this.state.hasError) {
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
              <button
                type="button"
                className={styles.primaryButton}
                onClick={() => window.location.reload()}
              >
                ページを再読み込み
              </button>
            </div>
            <p className={styles.description}>エラーID: {errorId}</p>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
