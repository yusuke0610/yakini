import { useEffect, useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";

import { getCurrentUser, setOnUnauthorized } from "./api";
import ErrorBoundary from "./components/ErrorBoundary";
import { useTheme } from "./hooks/useTheme";
import { AppRoutes, type AuthUser } from "./router";

/**
 * アプリケーションのメインエントリーポイントコンポーネント。
 * 認証状態を管理し、AppRoutes にルーティングを委譲する。
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
    <ErrorBoundary>
      <AppRoutes
        user={user}
        authLoading={authLoading}
        theme={theme}
        onToggleTheme={toggleTheme}
        githubError={githubError}
      />
    </ErrorBoundary>
  );
}
