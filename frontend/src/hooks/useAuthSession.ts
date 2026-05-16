import { useEffect, useRef, useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";

import { getCurrentUser, logout, setOnUnauthorized } from "../api";
import type { AuthUser } from "../router";

// 認証チェック不要なパス（未認証が正常な画面）
const PUBLIC_PATHS = new Set(["/", "/login", "/github/callback"]);

/**
 * アプリケーション全体の認証セッションを管理するカスタムフック。
 *
 * 責務:
 * - sessionStorage との同期（ページリロード時の復元）
 * - 401 を捕捉してログアウト状態へ遷移する onUnauthorized 登録
 * - URL クエリの ``github_error`` を取り込み、フックの利用者に渡す
 * - 初回マウント時に /auth/me で現在のユーザーを復元
 * - ログアウト直後の race condition 防止（``justLoggedOut`` フラグ）
 *
 * App.tsx を wiring のみに痩せさせ、認証ライフサイクルを単独でテスト可能にする。
 */
export function useAuthSession() {
  const navigate = useNavigate();
  const location = useLocation();

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
  const [authLoading, setAuthLoading] = useState(
    user === null && !PUBLIC_PATHS.has(location.pathname),
  );
  const [githubError, setGithubError] = useState<string | null>(null);

  // ログアウト直後の /auth/me 呼び出しを防ぐフラグ。
  // setUser(null) 前にセットし、effect が pathname より先に発火してもスキップできるようにする。
  const justLoggedOut = useRef(false);

  useEffect(() => {
    setOnUnauthorized(() => {
      sessionStorage.removeItem("auth_user");
      justLoggedOut.current = true;
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

    if (user || PUBLIC_PATHS.has(location.pathname) || justLoggedOut.current) {
      justLoggedOut.current = false;
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
  }, [user, location.pathname]);

  const handleLogout = async () => {
    await logout();
    sessionStorage.removeItem("auth_user");
    justLoggedOut.current = true;
    setUser(null);
  };

  const handleLoginSuccess = (rawUser: { username: string; is_github_user: boolean }) => {
    const authUser: AuthUser = {
      username: rawUser.username,
      isGitHubUser: rawUser.is_github_user,
    };
    sessionStorage.setItem("auth_user", JSON.stringify(authUser));
    setUser(authUser);
  };

  return {
    user,
    authLoading,
    githubError,
    handleLogout,
    handleLoginSuccess,
  };
}
