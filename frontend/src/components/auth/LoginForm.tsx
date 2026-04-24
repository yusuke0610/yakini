import { useState } from "react";

import { initiateGitHubLogin } from "../../api";
import shared from "../../styles/shared.module.css";
import styles from "./LoginForm.module.css";

export function LoginForm({
  githubError,
}: {
  githubError?: string | null;
}) {
  const [isLoading, setIsLoading] = useState(false);

  const handleGitHubLogin = async () => {
    setIsLoading(true);
    try {
      await initiateGitHubLogin(window.location.origin);
    } catch {
      setIsLoading(false);
    }
  };

  return (
    <div className={shared.page}>
      <main className={shared.container}>
        {isLoading ? (
          <div className={styles.githubLoadingContainer}>
            <div className={styles.spinner} />
            <p>GitHub認証へリダイレクト中...</p>
          </div>
        ) : (
          <div className={styles.loginBox}>
            <h1 className={styles.loginTitle}>DevForge</h1>
            <p className={styles.loginDescription}>GitHubアカウントでログインしてください</p>
            {githubError && <p className={styles.errorMessage}>{githubError}</p>}
            <div className={styles.loginActions}>
              <button
                type="button"
                className={styles.githubLogin}
                onClick={() => {
                  void handleGitHubLogin();
                }}
              >
                GitHubでログイン
              </button>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
