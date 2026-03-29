const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

let _onUnauthorized: (() => void) | null = null;

export function setOnUnauthorized(callback: () => void): void {
  _onUnauthorized = callback;
}

/** Cookie から CSRF トークンを取得する。 */
function getCsrfToken(): string {
  const match = document.cookie.match(/csrf_token=([^;]+)/);
  return match ? match[1] : "";
}

/** リフレッシュ中フラグ（複数の 401 が同時に来た場合の競合防止）。 */
let _isRefreshing = false;

/** リフレッシュ試行後のリトライかどうかを示すフラグ。 */
async function _tryRefresh(): Promise<boolean> {
  if (_isRefreshing) return false;
  _isRefreshing = true;
  try {
    const res = await fetch(`${API_BASE_URL}/auth/refresh`, {
      method: "POST",
      credentials: "include",
    });
    return res.ok;
  } catch {
    return false;
  } finally {
    _isRefreshing = false;
  }
}

/** エラーレスポンスの detail を取得する。 */
async function getErrorDetail(response: Response): Promise<string | null> {
  try {
    const body = await response.json();
    if (!body?.detail) return null;
    return typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
  } catch {
    return null;
  }
}

export async function request<T>(
  path: string,
  options: RequestInit = {},
  _isRetry = false,
): Promise<T> {
  const method = (options.method ?? "GET").toUpperCase();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...((options.headers as Record<string, string>) ?? {}),
  };

  // 状態変更リクエストには CSRF トークンを付与する
  if (["POST", "PUT", "DELETE", "PATCH"].includes(method)) {
    headers["X-CSRF-Token"] = getCsrfToken();
  }

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      headers,
      credentials: "include",
    });
  } catch {
    throw new Error("サーバーに接続できません。ネットワーク接続を確認してください。");
  }

  if (response.status === 401 && !_isRetry) {
    // リフレッシュトークンで再発行を試みる（1回のみ）
    const refreshed = await _tryRefresh();
    if (refreshed) {
      return request<T>(path, options, true);
    }
    _onUnauthorized?.();
    throw new Error("認証が必要です。再度ログインしてください。");
  }

  if (response.status === 401) {
    _onUnauthorized?.();
    throw new Error("認証が必要です。再度ログインしてください。");
  }

  if (response.status >= 500) {
    const detail = await getErrorDetail(response);
    if (detail) {
      throw new Error(detail);
    }
    const messages: Record<number, string> = {
      502: "サーバーとの通信に失敗しました。しばらくしてから再度お試しください。",
      503: "サーバーが一時的に利用できません。しばらくしてから再度お試しください。",
      504: "サーバーからの応答がタイムアウトしました。しばらくしてから再度お試しください。",
    };
    throw new Error(
      messages[response.status] ??
        "サーバーエラーが発生しました。しばらくしてから再度お試しください。",
    );
  }

  if (!response.ok) {
    const message = (await getErrorDetail(response)) ?? "リクエストの処理に失敗しました。";
    throw new Error(message);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

export { API_BASE_URL };
