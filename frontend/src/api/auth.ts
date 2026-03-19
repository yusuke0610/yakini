import { request, API_BASE_URL } from "./client";

type AuthResponse = { username: string; is_github_user: boolean };
type GitHubLoginUrlResponse = { authorization_url: string };

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

export async function getCurrentUser(): Promise<AuthResponse | null> {
  const response = await fetch(`${API_BASE_URL}/auth/me`, {
    credentials: "include",
  });
  if (response.status === 401) {
    return null;
  }
  if (!response.ok) {
    throw new Error("ログイン状態の確認に失敗しました。");
  }
  return (await response.json()) as AuthResponse;
}

export async function getGitHubLoginUrl(): Promise<string> {
  const response = await fetch(`${API_BASE_URL}/auth/github/login-url`, {
    credentials: "include",
  });
  if (!response.ok) {
    let message = "GitHub認証の開始に失敗しました。";
    try {
      const body = await response.json();
      if (typeof body.detail === "string") {
        message = body.detail;
      }
    } catch {
      // ignore
    }
    throw new Error(message);
  }
  const result = (await response.json()) as GitHubLoginUrlResponse;
  return result.authorization_url;
}
