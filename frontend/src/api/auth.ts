import { API_BASE_URL } from "./client";

type AuthResponse = { username: string; is_github_user: boolean };

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

export function getGitHubLoginUrl(returnTo: string): string {
  const params = new URLSearchParams({ return_to: returnTo });
  return `${API_BASE_URL}/auth/github/login?${params.toString()}`;
}
