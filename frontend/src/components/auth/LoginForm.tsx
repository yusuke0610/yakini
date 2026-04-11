import { useEffect } from "react";

import { getGitHubLoginUrl } from "../../api";
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
      window.location.assign(getGitHubLoginUrl(window.location.origin));
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
