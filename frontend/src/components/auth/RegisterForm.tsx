import { FormEvent, useState } from "react";

import { register } from "../../api";
import shared from "../../styles/shared.module.css";
import { PasswordInput } from "./PasswordInput";

export function RegisterForm({
  onLogin,
  onSwitchToLogin,
}: {
  onLogin: (username: string, isGitHubUser: boolean) => void;
  onSwitchToLogin: () => void;
}) {
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [passwordConfirm, setPasswordConfirm] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (password !== passwordConfirm) {
      setError("パスワードが一致しません。");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const result = await register(username, email, password);
      onLogin(result.username, result.is_github_user);
    } catch (err) {
      const message = err instanceof Error ? err.message : "登録に失敗しました。";
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={shared.page}>
      <main className={shared.container}>
        <header>
          <h1>新規登録</h1>
        </header>
        <form onSubmit={onSubmit} className={shared.form}>
          <section className={shared.section}>
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
              パスワード（8文字以上、英大文字・小文字・数字を含む）
              <PasswordInput
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="new-password"
                minLength={8}
              />
            </label>
            <label>
              パスワード（確認）
              <PasswordInput
                value={passwordConfirm}
                onChange={(e) => setPasswordConfirm(e.target.value)}
                autoComplete="new-password"
                minLength={8}
              />
            </label>
          </section>
          <div className={shared.actions}>
            <button type="submit" disabled={loading}>
              {loading ? "登録中..." : "登録"}
            </button>
          </div>
          {error && <p className={shared.error}>{error}</p>}
          <div className={shared.authLink}>
            <button type="button" onClick={onSwitchToLogin}>
              ログインに戻る
            </button>
          </div>
        </form>
      </main>
    </div>
  );
}
