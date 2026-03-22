import { useNavigate } from "react-router-dom";

import { LoginForm } from "../components/auth/LoginForm";

export default function LoginPage({
  onLogin,
  githubError,
}: {
  onLogin: (username: string, isGitHubUser: boolean) => void;
  githubError: string | null;
}) {
  const navigate = useNavigate();

  return (
    <LoginForm
      onLogin={onLogin}
      onSwitchToRegister={() => navigate("/signin")}
      githubError={githubError}
    />
  );
}
