import { useNavigate } from "react-router-dom";

import { RegisterForm } from "../components/auth/RegisterForm";

export default function SignInPage({
  onLogin,
}: {
  onLogin: (username: string, isGitHubUser: boolean) => void;
}) {
  const navigate = useNavigate();

  return (
    <RegisterForm
      onLogin={onLogin}
      onSwitchToLogin={() => navigate("/login")}
    />
  );
}
