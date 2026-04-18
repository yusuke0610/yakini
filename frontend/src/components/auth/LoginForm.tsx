import { useEffect } from "react";

import { initiateGitHubLogin } from "../../api";
import shared from "../../styles/shared.module.css";
import styles from "./LoginForm.module.css";

export function LoginForm({
  githubError,
}: {
  githubError?: string | null;
}) {

  useEffect(() => {
    // エラーがなければ自動的に GitHub OAuth へリダイレクトする
    if (!githubError) {
      initiateGitHubLogin(window.location.origin).catch(() => {
        window.location.reload();
      });
    }
  }, [githubError]);

  if (!githubError) {
    return (
      <div className={shared.page}>
        <main className={shared.container}>
          <div className={styles.githubLoadingContainer}>
            <div className={styles.spinner} />
            <p>GitHub認証へリダイレクト中...</p>
          </div>
        </main>
      </div>
    );
  }
}
