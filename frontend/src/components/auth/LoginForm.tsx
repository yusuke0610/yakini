import { FormEvent, useState } from "react";

import { getGitHubOAuthUrl, login } from "../../api";
import shared from "../../styles/shared.module.css";
import { PasswordInput } from "./PasswordInput";
import styles from "./LoginForm.module.css";

export function LoginForm({
  onLogin,
  onSwitchToRegister,
  githubError,
  githubLoading,
}: {
  onLogin: (username: string, isGitHubUser: boolean) => void;
  onSwitchToRegister: () => void;
  githubError?: string | null;
  githubLoading?: boolean;
}) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const result = await login(email, password);
      onLogin(result.username, result.is_github_user);
    } catch (err) {
      const message = err instanceof Error ? err.message : "ログインに失敗しました。";
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  if (githubLoading) {
    return (
      <div className={shared.page}>
        <main className={shared.container}>
          <div className={styles.githubLoadingContainer}>
            <div className={styles.spinner} />
            <p>GitHub認証中...</p>
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
        <form onSubmit={onSubmit} className={shared.form}>
          <section className={shared.section}>
            <label>
              メールアドレス
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoComplete="email"
              />
            </label>
            <label>
              パスワード
              <PasswordInput
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
              />
            </label>
          </section>
          <div className={styles.loginActions}>
            <button type="submit" disabled={loading}>
              {loading ? "ログイン中..." : "ログイン"}
            </button>
            <button
              type="button"
              className={styles.githubLogin}
              onClick={() => {
                window.location.href = getGitHubOAuthUrl();
              }}
            >
              Login with GitHub
            </button>
          </div>
          {(error || githubError) && <p className={shared.error}>{error || githubError}</p>}
          <div className={shared.authLink}>
            <button type="button" onClick={onSwitchToRegister}>
              新規登録はこちら
            </button>
          </div>
        </form>
      </main>
    </div>
  );
}
