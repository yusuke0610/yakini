import { useEffect, useRef } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";

import { handleGitHubCallback } from "../api/auth";
import shared from "../styles/shared.module.css";

type Props = {
  onLoginSuccess: (user: { username: string; is_github_user: boolean }) => void;
};

export default function GitHubCallbackPage({ onLoginSuccess }: Props) {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const calledRef = useRef(false);

  useEffect(() => {
    if (calledRef.current) return;
    calledRef.current = true;

    const code = searchParams.get("code");
    const state = searchParams.get("state");

    if (!code || !state) {
      navigate("/login?github_error=invalid_callback", { replace: true });
      return;
    }

    handleGitHubCallback(code, state)
      .then((user) => {
        onLoginSuccess(user);
        navigate("/", { replace: true });
      })
      .catch(() => {
        navigate("/login?github_error=authentication_failed", { replace: true });
      });
  }, [searchParams, navigate, onLoginSuccess]);

  return (
    <div className={shared.loadingOverlay}>
      <div className={shared.loadingSpinner} />
      <p className={shared.loadingText}>GitHubログイン処理中...</p>
    </div>
  );
}
