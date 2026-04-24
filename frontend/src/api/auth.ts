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

/** Firebase Hosting proxy 経由では 303 の Set-Cookie が除去されるため、
 *  200 JSON エンドポイントを fetch して state cookie をセットしてから GitHub へ遷移する。 */
export async function initiateGitHubLogin(returnTo: string): Promise<void> {
  const params = new URLSearchParams({ return_to: returnTo });
  const response = await fetch(`${API_BASE_URL}/auth/github/login-url?${params.toString()}`, {
    credentials: "include",
  });
  if (!response.ok) throw new Error("GitHub OAuth の開始に失敗しました");
  const data = (await response.json()) as { authorization_url: string };
  window.location.assign(data.authorization_url);
}

/** サーバー側で refresh_jti を無効化し Cookie を削除する。
 *  401 ハンドラのループを避けるため request ラッパーではなく fetch を直接使う。 */
export async function logout(): Promise<void> {
  await fetch(`${API_BASE_URL}/auth/logout`, {
    method: "POST",
    credentials: "include",
  });
}
