import { useEffect, useState } from "react";

import { setAuthToken, setOnUnauthorized, githubCallback } from "./api";
import type { PageKey } from "./formTypes";
import { LoginForm } from "./components/auth/LoginForm";
import { RegisterForm } from "./components/auth/RegisterForm";
import { BasicInfoForm } from "./components/forms/BasicInfoForm";
import { CareerResumeForm } from "./components/forms/CareerResumeForm";
import { ResumeForm } from "./components/forms/ResumeForm";

export default function App() {
  const [token, setToken] = useState<string | null>(() => {
    const saved = localStorage.getItem("auth_token");
    if (saved) {
      setAuthToken(saved);
    }
    return saved;
  });
  const [githubError, setGithubError] = useState<string | null>(null);
  const [githubLoading, setGithubLoading] = useState(() => {
    const params = new URLSearchParams(window.location.search);
    return !!params.get("code") && !localStorage.getItem("auth_token");
  });
  const [page, setPage] = useState<PageKey>(() => {
    const saved = sessionStorage.getItem("current_page");
    return saved === "career" || saved === "Resume" ? saved : "basic";
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

  const handleLogin = (newToken: string) => {
    localStorage.setItem("auth_token", newToken);
    setAuthToken(newToken);
    setToken(newToken);
    setPage("basic");
  };

  const handleLogout = () => {
    localStorage.removeItem("auth_token");
    sessionStorage.removeItem("current_page");
    setAuthToken(null);
    setToken(null);
    setAuthMode("login");
  };

  useEffect(() => {
    setOnUnauthorized(() => {
      localStorage.removeItem("auth_token");
      setAuthToken(null);
      setToken(null);
    });

    // Handle GitHub OAuth callback
    const params = new URLSearchParams(window.location.search);
    const code = params.get("code");
    const saved = localStorage.getItem("auth_token");
    if (code && !saved) {
      window.history.replaceState({}, "", window.location.pathname);
      setGithubLoading(true);
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

  if (!token) {
    if (authMode === "register") {
      return <RegisterForm onLogin={handleLogin} onSwitchToLogin={() => setAuthMode("login")} />;
    }
    return <LoginForm onLogin={handleLogin} onSwitchToRegister={() => setAuthMode("register")} githubError={githubError} githubLoading={githubLoading} />;
  }

  return (
    <div className="page">
      <div className="appLayout">
        <aside className="sidebar">
          <p className="sidebarTitle">DevForge</p>
          <nav className="sidebarNav">
            <button
              type="button"
              className={`sidebarItem ${page === "basic" ? "active" : ""}`}
              onClick={() => setPage("basic")}
            >
              基本情報
            </button>
            <button
              type="button"
              className={`sidebarItem ${page === "career" ? "active" : ""}`}
              onClick={() => setPage("career")}
            >
              職務経歴書
            </button>
            <button
              type="button"
              className={`sidebarItem ${page === "Resume" ? "active" : ""}`}
              onClick={() => setPage("Resume")}
            >
              履歴書
            </button>
          </nav>
          <div className="sidebarLogout">
            <button type="button" className="sidebarItem" onClick={handleLogout}>
              ログアウト
            </button>
          </div>
        </aside>

        <main className="mainContent">
          {page === "basic" && <BasicInfoForm />}
          {page === "career" && <CareerResumeForm />}
          {page === "Resume" && <ResumeForm />}
        </main>
      </div>
    </div>
  );
}
