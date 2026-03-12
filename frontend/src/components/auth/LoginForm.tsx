import { FormEvent, useState } from "react";

import { getGitHubOAuthUrl, login } from "../../api";
import { PasswordInput } from "./PasswordInput";

export function LoginForm({
  onLogin,
  onSwitchToRegister,
}: {
  onLogin: (token: string) => void;
  onSwitchToRegister: () => void;
}) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const result = await login(username, password);
      onLogin(result.access_token);
    } catch (err) {
      const message = err instanceof Error ? err.message : "ログインに失敗しました。";
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page">
      <main className="container">
        <header className="topHeader">
          <h1>ログイン</h1>
        </header>
        <form onSubmit={onSubmit} className="form">
          <section className="section">
            <label>
              ユーザー名
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                autoComplete="username"
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
          <div className="loginActions">
            <button type="submit" disabled={loading}>
              {loading ? "ログイン中..." : "ログイン"}
            </button>
            <button
              type="button"
              className="githubLogin"
              onClick={() => {
                window.location.href = getGitHubOAuthUrl();
              }}
            >
              Login with GitHub
            </button>
          </div>
          {error && <p className="error">{error}</p>}
          <div className="authLink">
            <button type="button" onClick={onSwitchToRegister}>
              新規登録はこちら
            </button>
          </div>
        </form>
      </main>
    </div>
  );
}
