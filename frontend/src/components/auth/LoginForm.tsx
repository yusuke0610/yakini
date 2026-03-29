import { useEffect, useState } from "react";

import { getGitHubLoginUrl } from "../../api";
import shared from "../../styles/shared.module.css";
import styles from "./LoginForm.module.css";

export function LoginForm({
  githubError,
}: {
  githubError?: string | null;
}) {
  const [githubLoading, setGithubLoading] = useState(false);

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

  return (
    <div className={shared.page}>
      <main className={shared.container}>
        <header>
          <h1>ログイン</h1>
        </header>
        <p className={shared.error}>{githubError}</p>
        <div className={styles.loginActions}>
          <button
            type="button"
            className={styles.githubLogin}
            disabled={githubLoading}
            onClick={() => {
              setGithubLoading(true);
              window.location.assign(getGitHubLoginUrl(window.location.href));
            }}
          >
            {githubLoading ? "GitHubへ接続中..." : "Login with GitHub"}
          </button>
        </div>
      </main>
    </div>
  );
}
