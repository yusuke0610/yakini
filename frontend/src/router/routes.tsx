import { Route, Routes, Navigate } from "react-router-dom";

import type { Theme } from "../hooks/useTheme";
import { AuthenticatedLayout } from "../components/AuthenticatedLayout";
import { PrivateRoute, PublicRoute, type AuthUser } from "./guards";
import CareerAnalysisPage from "../pages/CareerAnalysisPage";
import CareerPage from "../pages/CareerPage";
import GitHubIntelligencePage from "../pages/GitHubIntelligencePage";
import BlogPage from "../pages/BlogPage";
import GitHubCallbackPage from "../pages/GitHubCallbackPage";
import LoginPage from "../pages/LoginPage";
import NotFoundPage from "../pages/NotFoundPage";

type AppRoutesProps = {
  user: AuthUser | null;
  authLoading: boolean;
  theme: Theme;
  onToggleTheme: () => void;
  githubError: string | null;
  onLogout: () => void;
  onLoginSuccess: (user: { username: string; is_github_user: boolean }) => void;
};

/**
 * アプリケーション全体のルート定義。
 * パスとページコンポーネントの対応を管理する。
 */
export default function AppRoutes({
  user,
  authLoading,
  theme,
  onToggleTheme,
  githubError,
  onLogout,
  onLoginSuccess,
}: AppRoutesProps) {
  return (
    <Routes>
      {/* 未認証ルート */}
      <Route element={<PublicRoute user={user} authLoading={authLoading} />}>
        <Route path="/login" element={<LoginPage githubError={githubError} />} />
      </Route>

      {/* 認証済みルート */}
      <Route element={<PrivateRoute user={user} authLoading={authLoading} />}>
        <Route
          element={
            <AuthenticatedLayout
              user={user!}
              theme={theme}
              onToggleTheme={onToggleTheme}
              onLogout={onLogout}
            />
          }
        >
          <Route path="/career" element={<CareerPage />} />
          <Route path="/github_intelligence" element={<GitHubIntelligencePage />} />
          <Route path="/blog" element={<BlogPage />} />
          <Route path="/career_analysis" element={<CareerAnalysisPage />} />
        </Route>
      </Route>

      {/*
        GitHub OAuth コールバック: Firebase Hosting の /auth/** rewrite に巻き込まれて
        Cloud Run へ転送されないように、/github/callback で受け取る。
      */}
      <Route
        path="/github/callback"
        element={<GitHubCallbackPage onLoginSuccess={onLoginSuccess} />}
      />

      <Route path="/" element={<Navigate to="/career" replace />} />
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}
