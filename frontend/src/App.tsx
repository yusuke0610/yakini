import { useEffect, useState } from "react";

import { getCurrentUser, logout, setOnUnauthorized } from "./api";
import type { PageKey } from "./formTypes";
import { useTheme } from "./hooks/useTheme";
import { LoginForm } from "./components/auth/LoginForm";
import { RegisterForm } from "./components/auth/RegisterForm";
import { UserMenu } from "./components/UserMenu";
import { BasicInfoForm } from "./components/forms/BasicInfoForm";
import { CareerResumeForm } from "./components/forms/CareerResumeForm";
import { ResumeForm } from "./components/forms/ResumeForm";
import { GitHubAnalysisPage } from "./components/analysis/GitHubAnalysisPage";
import { BlogPage } from "./components/blog/BlogPage";
import shared from "./styles/shared.module.css";
import styles from "./App.module.css";

type AuthUser = { username: string; isGitHubUser: boolean };

/**
 * アプリケーションのメインエントリーポイントコンポーネント。
 * 認証状態、テーマ、およびページルーティングを管理します。
 */
export default function App() {
  const { theme, toggleTheme } = useTheme();
  const [user, setUser] = useState<AuthUser | null>(() => {
    const saved = sessionStorage.getItem("auth_user");
    if (saved) {
      try {
        return JSON.parse(saved) as AuthUser;
      } catch {
        return null;
      }
    }
    return null;
  });
  const [authLoading, setAuthLoading] = useState(user === null);
  const [githubError, setGithubError] = useState<string | null>(null);
  const [page, setPage] = useState<PageKey>(() => {
    const saved = sessionStorage.getItem("current_page");
    if (saved === "career" || saved === "Resume" || saved === "blog") return saved;
    if (saved === "github" && user?.isGitHubUser) return saved;
    return "basic";
  });
  const [authMode, setAuthMode] = useState<"login" | "register">(() => {
    return sessionStorage.getItem("auth_mode") === "register" ? "register" : "login";
  });

  useEffect(() => {
    sessionStorage.setItem("current_page", page);
  }, [page]);

  useEffect(() => {
    sessionStorage.setItem("auth_mode", authMode);
  }, [authMode]);

  const clearAuthenticatedUser = () => {
    sessionStorage.removeItem("auth_user");
    sessionStorage.removeItem("current_page");
    setUser(null);
  };

  /**
   * ログイン成功時の処理。
   */
  const setAuthenticatedUser = (
    username: string,
    isGitHubUser: boolean,
    resetPage: boolean,
  ) => {
    const authUser: AuthUser = { username, isGitHubUser };
    sessionStorage.setItem("auth_user", JSON.stringify(authUser));
    setUser(authUser);
    if (resetPage) {
      setPage("basic");
    }
  };

  const handleLogin = (username: string, isGitHubUser: boolean) => {
    setAuthenticatedUser(username, isGitHubUser, true);
  };

  /**
   * ログアウト処理。
   */
  const handleLogout = () => {
    logout();
    clearAuthenticatedUser();
    setAuthMode("login");
  };

  useEffect(() => {
    setOnUnauthorized(() => {
      sessionStorage.removeItem("auth_user");
      sessionStorage.removeItem("current_page");
      setUser(null);
    });
  }, []);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const error = params.get("github_error");
    if (error) {
      window.history.replaceState({}, "", window.location.pathname);
      setGithubError(error);
    }
  }, []);

  useEffect(() => {
    let active = true;

    if (user) {
      setAuthLoading(false);
      return () => {
        active = false;
      };
    }

    (async () => {
      try {
        const currentUser = await getCurrentUser();
        if (!active || !currentUser) return;
        const authUser: AuthUser = {
          username: currentUser.username,
          isGitHubUser: currentUser.is_github_user,
        };
        sessionStorage.setItem("auth_user", JSON.stringify(authUser));
        setUser(authUser);
      } catch {
        if (!active) return;
      } finally {
        if (active) {
          setAuthLoading(false);
        }
      }
    })();

    return () => {
      active = false;
    };
  }, [user]);

  if (authLoading) {
    return (
      <div className={shared.page}>
        <main className={shared.container}>
          <p>認証状態を確認中...</p>
        </main>
      </div>
    );
  }

  if (!user) {
    if (authMode === "register") {
      return <RegisterForm onLogin={handleLogin} onSwitchToLogin={() => setAuthMode("login")} />;
    }
    return <LoginForm onLogin={handleLogin} onSwitchToRegister={() => setAuthMode("register")} githubError={githubError} />;
  }

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
            {user.isGitHubUser && (
              <button
                type="button"
                className={`${styles.sidebarItem} ${page === "github" ? styles.active : ""}`}
                onClick={() => setPage("github")}
              >
                GitHub分析
              </button>
            )}
            <button
              type="button"
              className={`${styles.sidebarItem} ${page === "blog" ? styles.active : ""}`}
              onClick={() => setPage("blog")}
            >
              ブログ連携
            </button>
          </nav>
          <div className={styles.sidebarFooter}>
            <UserMenu
              username={user.username}
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
          {page === "blog" && <BlogPage />}
        </main>
      </div>
    </div>
  );
}
