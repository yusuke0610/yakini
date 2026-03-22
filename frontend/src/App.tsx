import { ReactNode, useEffect, useState } from "react";
import { Routes, Route, Navigate, NavLink, useNavigate, useLocation } from "react-router-dom";

import { getCurrentUser, logout, setOnUnauthorized } from "./api";
import { useTheme, type Theme } from "./hooks/useTheme";
import { LoginForm } from "./components/auth/LoginForm";
import { RegisterForm } from "./components/auth/RegisterForm";
import { UserMenu } from "./components/UserMenu";
import { BasicInfoForm } from "./components/forms/BasicInfoForm";
import { CareerResumeForm } from "./components/forms/CareerResumeForm";
import { ResumeForm } from "./components/forms/ResumeForm";
import { GitHubAnalysisPage } from "./components/analysis/GitHubAnalysisPage";
import { BlogPage } from "./components/blog/BlogPage";
import { LoadingOverlay } from "./components/LoadingOverlay";
import shared from "./styles/shared.module.css";
import styles from "./App.module.css";

type AuthUser = { username: string; isGitHubUser: boolean };

/**
 * 認証済みユーザー専用のルートガード。
 * 未認証時は /login にリダイレクトする。
 */
function PrivateRoute({
  user,
  authLoading,
  children,
}: {
  user: AuthUser | null;
  authLoading: boolean;
  children: ReactNode;
}) {
  if (authLoading) return <LoadingOverlay />;
  if (!user) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

/**
 * 未認証ユーザー専用のルートガード。
 * 認証済み時は /basic_info にリダイレクトする。
 */
function PublicRoute({
  user,
  authLoading,
  children,
}: {
  user: AuthUser | null;
  authLoading: boolean;
  children: ReactNode;
}) {
  if (authLoading) return <LoadingOverlay />;
  if (user) return <Navigate to="/basic_info" replace />;
  return <>{children}</>;
}

/**
 * 認証済みユーザー向けのサイドバー付きレイアウト。
 * PrivateRoute でガードされた後にのみレンダリングされるため、user は非 null。
 */
function AuthenticatedLayout({
  user,
  theme,
  onToggleTheme,
  onLogout,
}: {
  user: AuthUser;
  theme: Theme;
  onToggleTheme: () => void;
  onLogout: () => void;
}) {
  return (
    <div className={shared.page}>
      <div className={styles.appLayout}>
        <aside className={styles.sidebar}>
          <p className={styles.sidebarTitle}>DevForge</p>
          <nav className={styles.sidebarNav}>
            <NavLink
              to="/basic_info"
              className={({ isActive }) =>
                `${styles.sidebarItem} ${isActive ? styles.active : ""}`
              }
            >
              基本情報
            </NavLink>
            <NavLink
              to="/career"
              className={({ isActive }) =>
                `${styles.sidebarItem} ${isActive ? styles.active : ""}`
              }
            >
              職務経歴書
            </NavLink>
            <NavLink
              to="/resume"
              className={({ isActive }) =>
                `${styles.sidebarItem} ${isActive ? styles.active : ""}`
              }
            >
              履歴書
            </NavLink>
            {user.isGitHubUser && (
              <NavLink
                to="/github_intelligence"
                className={({ isActive }) =>
                  `${styles.sidebarItem} ${isActive ? styles.active : ""}`
                }
              >
                GitHub分析
              </NavLink>
            )}
            <NavLink
              to="/blog"
              className={({ isActive }) =>
                `${styles.sidebarItem} ${isActive ? styles.active : ""}`
              }
            >
              ブログ連携
            </NavLink>
          </nav>
          <div className={styles.sidebarFooter}>
            <UserMenu
              username={user.username}
              theme={theme}
              onToggleTheme={onToggleTheme}
              onLogout={onLogout}
            />
          </div>
        </aside>

        <main className={styles.mainContent}>
          <Routes>
            <Route path="/basic_info" element={<BasicInfoForm />} />
            <Route path="/career" element={<CareerResumeForm />} />
            <Route path="/resume" element={<ResumeForm />} />
            <Route path="/github_intelligence" element={<GitHubAnalysisPage />} />
            <Route path="/blog" element={<BlogPage />} />
            <Route path="/" element={<Navigate to="/basic_info" replace />} />
            <Route path="*" element={<Navigate to="/basic_info" replace />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}

/**
 * アプリケーションのメインエントリーポイントコンポーネント。
 * 認証状態、テーマ、およびページルーティングを管理します。
 */
export default function App() {
  const navigate = useNavigate();
  const location = useLocation();
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

  const clearAuthenticatedUser = () => {
    sessionStorage.removeItem("auth_user");
    setUser(null);
  };

  /**
   * ログイン成功時の処理。
   */
  const handleLogin = (username: string, isGitHubUser: boolean) => {
    const authUser: AuthUser = { username, isGitHubUser };
    sessionStorage.setItem("auth_user", JSON.stringify(authUser));
    setUser(authUser);
    navigate("/basic_info", { replace: true });
  };

  /**
   * ログアウト処理。
   */
  const handleLogout = () => {
    logout();
    clearAuthenticatedUser();
    navigate("/login", { replace: true });
  };

  useEffect(() => {
    setOnUnauthorized(() => {
      sessionStorage.removeItem("auth_user");
      setUser(null);
    });
  }, []);

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const error = params.get("github_error");
    if (error) {
      navigate(location.pathname, { replace: true });
      setGithubError(error);
    }
  }, [location.search, location.pathname, navigate]);

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

  return (
    <Routes>
      {/* 未認証ルート */}
      <Route
        path="/login"
        element={
          <PublicRoute user={user} authLoading={authLoading}>
            <LoginForm
              onLogin={handleLogin}
              onSwitchToRegister={() => navigate("/signin")}
              githubError={githubError}
            />
          </PublicRoute>
        }
      />
      <Route
        path="/signin"
        element={
          <PublicRoute user={user} authLoading={authLoading}>
            <RegisterForm
              onLogin={handleLogin}
              onSwitchToLogin={() => navigate("/login")}
            />
          </PublicRoute>
        }
      />

      {/* 認証済みルート（共通レイアウト付き） */}
      <Route
        path="*"
        element={
          <PrivateRoute user={user} authLoading={authLoading}>
            <AuthenticatedLayout
              user={user!}
              theme={theme}
              onToggleTheme={toggleTheme}
              onLogout={handleLogout}
            />
          </PrivateRoute>
        }
      />
    </Routes>
  );
}
