import { useEffect, useState } from "react";

import { setAuthToken, setOnUnauthorized, githubCallback } from "./api";
import { parseUsernameFromToken } from "./auth-utils";
import type { PageKey } from "./formTypes";
import { useTheme } from "./hooks/useTheme";
import { LoginForm } from "./components/auth/LoginForm";
import { RegisterForm } from "./components/auth/RegisterForm";
import { UserMenu } from "./components/UserMenu";
import { BasicInfoForm } from "./components/forms/BasicInfoForm";
import { CareerResumeForm } from "./components/forms/CareerResumeForm";
import { ResumeForm } from "./components/forms/ResumeForm";
import { GitHubAnalysisPage } from "./components/analysis/GitHubAnalysisPage";
import shared from "./styles/shared.module.css";
import styles from "./App.module.css";

/**
 * アプリケーションのメインエントリーポイントコンポーネント。
 * 認証状態、テーマ、およびページルーティングを管理します。
 */
export default function App() {
  const { theme, toggleTheme } = useTheme();
  const [token, setToken] = useState<string | null>(() => {
    // ローカルストレージからトークンを復元
    const saved = localStorage.getItem("auth_token");
    if (saved) {
      setAuthToken(saved);
    }
    return saved;
  });

  const username = parseUsernameFromToken(token);
  const isGitHubUser = username?.startsWith("github:") ?? false;
  const [githubError, setGithubError] = useState<string | null>(null);
  const [githubLoading, setGithubLoading] = useState(() => {
    // GitHub OAuth コールバックの待機中かどうかを判定
    const params = new URLSearchParams(window.location.search);
    return !!params.get("code") && !localStorage.getItem("auth_token");
  });
  const [page, setPage] = useState<PageKey>(() => {
    // セッションストレージから現在のページを復元
    const saved = sessionStorage.getItem("current_page");
    if (saved === "career" || saved === "Resume") return saved;
    if (saved === "github" && isGitHubUser) return saved;
    return "basic";
  });
  const [authMode, setAuthMode] = useState<"login" | "register">(() => {
    // セッションストレージから認証モードを復元
    return sessionStorage.getItem("auth_mode") === "register" ? "register" : "login";
  });

  // ページ変更をセッションに保存
  useEffect(() => {
    sessionStorage.setItem("current_page", page);
  }, [page]);

  // 認証モード変更をセッションに保存
  useEffect(() => {
    sessionStorage.setItem("auth_mode", authMode);
  }, [authMode]);

  /**
   * ログイン成功時の処理。
   */
  const handleLogin = (newToken: string) => {
    localStorage.setItem("auth_token", newToken);
    setAuthToken(newToken);
    setToken(newToken);
    setPage("basic");
  };

  /**
   * ログアウト処理。
   */
  const handleLogout = () => {
    localStorage.removeItem("auth_token");
    sessionStorage.removeItem("current_page");
    setAuthToken(null);
    setToken(null);
    setAuthMode("login");
  };

  useEffect(() => {
    // 認証エラー（401）発生時のグローバルハンドラを設定
    setOnUnauthorized(() => {
      localStorage.removeItem("auth_token");
      setAuthToken(null);
      setToken(null);
    });

    // GitHub OAuth コールバックを処理
    const params = new URLSearchParams(window.location.search);
    const code = params.get("code");
    const saved = localStorage.getItem("auth_token");
    if (code && !saved) {
      // クエリパラメータをクリアしてリロード時の再実行を防止
      window.history.replaceState({}, "", window.location.pathname);
      // カスケードレンダリングを避けるために setTimeout を使用
      setTimeout(() => setGithubLoading(true), 0);
      githubCallback(code)
        .then((result) => {
          handleLogin(result.access_token);
        })
        .catch(() => {
          setGithubError("GitHub認証に失敗しました。もう一度お試しください。");
        })
        .finally(() => {
          setGithubLoading(false);
        });
    }
  }, []);

  // 非ログイン状態の表示
  if (!token) {
    if (authMode === "register") {
      return <RegisterForm onLogin={handleLogin} onSwitchToLogin={() => setAuthMode("login")} />;
    }
    return <LoginForm onLogin={handleLogin} onSwitchToRegister={() => setAuthMode("register")} githubError={githubError} githubLoading={githubLoading} />;
  }

  // メインアプリケーションレイアウト
  return (
    <div className={shared.page}>
      <div className={styles.appLayout}>
        <aside className={styles.sidebar}>
          <p className={styles.sidebarTitle}>DevForge</p>
          <nav className={styles.sidebarNav}>
            <button
              type="button"
              className={`${styles.sidebarItem} ${page === "basic" ? styles.active : ""}`}
              onClick={() => setPage("basic")}
            >
              基本情報
            </button>
            <button
              type="button"
              className={`${styles.sidebarItem} ${page === "career" ? styles.active : ""}`}
              onClick={() => setPage("career")}
            >
              職務経歴書
            </button>
            <button
              type="button"
              className={`${styles.sidebarItem} ${page === "Resume" ? styles.active : ""}`}
              onClick={() => setPage("Resume")}
            >
              履歴書
            </button>
            {isGitHubUser && (
              <button
                type="button"
                className={`${styles.sidebarItem} ${page === "github" ? styles.active : ""}`}
                onClick={() => setPage("github")}
              >
                GitHub分析
              </button>
            )}
          </nav>
          <div className={styles.sidebarFooter}>
            <UserMenu
              username={username}
              theme={theme}
              onToggleTheme={toggleTheme}
              onLogout={handleLogout}
            />
          </div>
        </aside>

        <main className={styles.mainContent}>
          {page === "basic" && <BasicInfoForm />}
          {page === "career" && <CareerResumeForm />}
          {page === "Resume" && <ResumeForm />}
          {page === "github" && <GitHubAnalysisPage />}
        </main>
      </div>
    </div>
  );
}
