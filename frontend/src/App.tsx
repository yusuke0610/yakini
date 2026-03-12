import { useEffect, useState } from "react";

import { setAuthToken, setOnUnauthorized, githubCallback } from "./api";
import type { PageKey } from "./formTypes";
import { LoginForm } from "./components/auth/LoginForm";
import { RegisterForm } from "./components/auth/RegisterForm";
import { BasicInfoForm } from "./components/forms/BasicInfoForm";
import { CareerResumeForm } from "./components/forms/CareerResumeForm";
import { ResumeForm } from "./components/forms/ResumeForm";

export default function App() {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem("auth_token"));
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
    const saved = localStorage.getItem("auth_token");
    if (saved) {
      setAuthToken(saved);
    }
    setOnUnauthorized(() => {
      localStorage.removeItem("auth_token");
      setAuthToken(null);
      setToken(null);
    });

    // Handle GitHub OAuth callback
    const params = new URLSearchParams(window.location.search);
    const code = params.get("code");
    if (code && !saved) {
      window.history.replaceState({}, "", window.location.pathname);
      githubCallback(code)
        .then((result) => {
          handleLogin(result.access_token);
        })
        .catch(() => {
          // GitHub OAuth failed, user can retry
        });
    }
  }, []);

  if (!token) {
    if (authMode === "register") {
      return <RegisterForm onLogin={handleLogin} onSwitchToLogin={() => setAuthMode("login")} />;
    }
    return <LoginForm onLogin={handleLogin} onSwitchToRegister={() => setAuthMode("register")} />;
  }

  return (
    <div className="page">
      <main className="container">
        <header className="topHeader">
          <h1>{page === "basic" ? "基本情報" : page === "career" ? "職務経歴書" : "履歴書"}</h1>
          <div className="tabRow">
            <button
              type="button"
              className={`tabButton ${page === "basic" ? "active" : ""}`}
              onClick={() => setPage("basic")}
            >
              基本情報
            </button>
            <button
              type="button"
              className={`tabButton ${page === "career" ? "active" : ""}`}
              onClick={() => setPage("career")}
            >
              職務経歴書
            </button>
            <button
              type="button"
              className={`tabButton ${page === "Resume" ? "active" : ""}`}
              onClick={() => setPage("Resume")}
            >
              履歴書
            </button>
            <button type="button" className="tabButton" onClick={handleLogout}>
              ログアウト
            </button>
          </div>
        </header>

        <section hidden={page !== "basic"} className="pagePanel" aria-hidden={page !== "basic"}>
          <BasicInfoForm />
        </section>
        <section hidden={page !== "career"} className="pagePanel" aria-hidden={page !== "career"}>
          <CareerResumeForm />
        </section>
        <section hidden={page !== "Resume"} className="pagePanel" aria-hidden={page !== "Resume"}>
          <ResumeForm />
        </section>
      </main>
    </div>
  );
}
