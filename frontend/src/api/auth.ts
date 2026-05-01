import { API_BASE_URL, request } from "./client";

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

export async function handleGitHubCallback(code: string, state: string): Promise<AuthResponse> {
  return request<AuthResponse>("/auth/github/callback", {
    method: "POST",
    body: JSON.stringify({ code, state }),
  });
}

/** sessionStorage の key。CSRF 検証用に GitHub OAuth state を保持する。 */
export const GITHUB_OAUTH_STATE_STORAGE_KEY = "github_oauth_state";

/** Firebase Hosting は __session 以外の Cookie を Cloud Run に転送せず、
 *  さらに /auth/** rewrite の影響でフロントの React ルートにも到達できないため、
 *  state は sessionStorage で管理し、コールバック URL は /github/callback に揃える。 */
export async function initiateGitHubLogin(returnTo: string): Promise<void> {
  const params = new URLSearchParams({ return_to: returnTo });
  const response = await fetch(`${API_BASE_URL}/auth/github/login-url?${params.toString()}`, {
    credentials: "include",
  });
  if (!response.ok) throw new Error("GitHub OAuth の開始に失敗しました");
  const data = (await response.json()) as { authorization_url: string; state: string };
  // CSRF 検証用に state を sessionStorage へ保存する（コールバックで照合）
  sessionStorage.setItem(GITHUB_OAUTH_STATE_STORAGE_KEY, data.state);
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
