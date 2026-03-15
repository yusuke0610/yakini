import { request, API_BASE_URL } from "./client";

type AuthResponse = { username: string; is_github_user: boolean };

export function login(email: string, password: string): Promise<AuthResponse> {
  return request("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export function register(
  username: string,
  email: string,
  password: string,
): Promise<AuthResponse> {
  return request("/auth/register", {
    method: "POST",
    body: JSON.stringify({ username, email, password }),
  });
}

export async function logout(): Promise<void> {
  await fetch(`${API_BASE_URL}/auth/logout`, {
    method: "POST",
    credentials: "include",
  });
}

export function getGitHubOAuthUrl(): string {
  const clientId = import.meta.env.VITE_GITHUB_CLIENT_ID ?? "";
  const redirectUri = `${window.location.origin}/`;
  const state = crypto.randomUUID();
  sessionStorage.setItem("github_oauth_state", state);
  return `https://github.com/login/oauth/authorize?client_id=${clientId}&redirect_uri=${encodeURIComponent(redirectUri)}&scope=read:user&state=${encodeURIComponent(state)}`;
}

export function verifyOAuthState(state: string): boolean {
  const saved = sessionStorage.getItem("github_oauth_state");
  sessionStorage.removeItem("github_oauth_state");
  return saved === state;
}

export function githubCallback(
  code: string,
  state: string,
): Promise<AuthResponse> {
  return request("/auth/github/callback", {
    method: "POST",
    body: JSON.stringify({ code, state }),
  });
}
