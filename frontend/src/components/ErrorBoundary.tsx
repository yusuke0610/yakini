import { Component, type ErrorInfo, type ReactNode } from "react";

import styles from "./ErrorBoundary.module.css";

type ErrorBoundaryProps = {
  children: ReactNode;
};

type ErrorBoundaryState = {
  hasError: boolean;
};

export default class ErrorBoundary extends Component<
  ErrorBoundaryProps,
  ErrorBoundaryState
> {
  state: ErrorBoundaryState = {
    hasError: false,
  };

  static getDerivedStateFromError(): ErrorBoundaryState {
    return { hasError: true };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    console.error("Unhandled render error", error, errorInfo);
  }

  private handleGoHome = (): void => {
    window.location.href = "/basic_info";
  };

  private handleReload = (): void => {
    window.location.reload();
  };

  render(): ReactNode {
    if (!this.state.hasError) {
      return this.props.children;
    }

    return (
      <div className={styles.root}>
        <div className={styles.card}>
          <p className={styles.eyebrow}>Application Error</p>
          <h1 className={styles.title}>予期しないエラーが発生しました</h1>
          <p className={styles.description}>
            ページの表示中に問題が発生しました。再読み込みするか、ホームへ戻ってください。
          </p>
          <div className={styles.actions}>
            <button type="button" className={styles.secondaryButton} onClick={this.handleGoHome}>
              ホームに戻る
            </button>
            <button type="button" className={styles.primaryButton} onClick={this.handleReload}>
              ページを再読み込み
            </button>
          </div>
        </div>
      </div>
    );
  }
}
