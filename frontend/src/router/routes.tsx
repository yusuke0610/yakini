import { Route, Routes, Navigate } from "react-router-dom";

import type { Theme } from "../hooks/useTheme";
import { AuthenticatedLayout } from "../components/AuthenticatedLayout";
import { PrivateRoute, PublicRoute, type AuthUser } from "./guards";
import BasicInfoPage from "../pages/BasicInfoPage";
import CareerPage from "../pages/CareerPage";
import ResumePage from "../pages/ResumePage";
import GitHubIntelligencePage from "../pages/GitHubIntelligencePage";
import BlogPage from "../pages/BlogPage";
import LoginPage from "../pages/LoginPage";
import SignInPage from "../pages/SignInPage";

type AppRoutesProps = {
  user: AuthUser | null;
  authLoading: boolean;
  theme: Theme;
  onToggleTheme: () => void;
  onLogin: (username: string, isGitHubUser: boolean) => void;
  onLogout: () => void;
  githubError: string | null;
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
  onLogin,
  onLogout,
  githubError,
}: AppRoutesProps) {
  return (
    <Routes>
      {/* 未認証ルート */}
      <Route element={<PublicRoute user={user} authLoading={authLoading} />}>
        <Route path="/login" element={<LoginPage onLogin={onLogin} githubError={githubError} />} />
        <Route path="/signin" element={<SignInPage onLogin={onLogin} />} />
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
          <Route path="/basic_info" element={<BasicInfoPage />} />
          <Route path="/career" element={<CareerPage />} />
          <Route path="/resume" element={<ResumePage />} />
          <Route path="/github_intelligence" element={<GitHubIntelligencePage />} />
          <Route path="/blog" element={<BlogPage />} />
        </Route>
      </Route>

      <Route path="/" element={<Navigate to="/basic_info" replace />} />
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  );
}
