const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

let _onUnauthorized: (() => void) | null = null;

export function setOnUnauthorized(callback: () => void): void {
  _onUnauthorized = callback;
}

export async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...((options.headers as Record<string, string>) ?? {}),
  };

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

  if (response.status === 401) {
    _onUnauthorized?.();
  }

  if (response.status >= 500) {
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
    let message = "リクエストの処理に失敗しました。";
    try {
      const body = await response.json();
      if (body.detail) {
        message = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
      }
    } catch {
      // JSONパース失敗時はデフォルトメッセージを使う
    }
    throw new Error(message);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

export { API_BASE_URL };
