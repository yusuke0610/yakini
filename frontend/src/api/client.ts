import { ERROR_CONFIG } from "../constants/errorMessages";
import { ApiError } from "../utils/appError";
import { generateErrorId } from "../utils/errorId";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "";

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

type ErrorResponseBody = {
  code?: string;
  message?: string;
  action?: string | null;
  retry_after?: number | null;
  error_id?: string | null;
  detail?: unknown;
};

async function getErrorBody(response: Response): Promise<ErrorResponseBody | null> {
  try {
    return (await response.json()) as ErrorResponseBody;
  } catch {
    return null;
  }
}

function getLegacyDetail(body: ErrorResponseBody | null): string | null {
  if (!body?.detail) return null;
  return typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
}

function buildApiError(response: Response, body: ErrorResponseBody | null, fallbackMessage: string): ApiError {
  const code =
    body?.code ??
    (response.status === 401
      ? "AUTH_REQUIRED"
      : response.status === 429
        ? "RATE_LIMITED"
        : response.status >= 500
          ? "INTERNAL_ERROR"
          : "VALIDATION_ERROR");
  const message =
    body?.message ??
    getLegacyDetail(body) ??
    ERROR_CONFIG[code]?.message ??
    fallbackMessage;

  return new ApiError({
    code,
    message,
    action: body?.action ?? null,
    retryAfter:
      typeof body?.retry_after === "number" ? body.retry_after : null,
    errorId:
      typeof body?.error_id === "string" && body.error_id
        ? body.error_id
        : generateErrorId(),
  });
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
    throw new ApiError({
      code: "INTERNAL_ERROR",
      message: "サーバーに接続できません。ネットワーク接続を確認してください。",
    });
  }

  if (response.status === 401 && !_isRetry) {
    // リフレッシュトークンで再発行を試みる（1回のみ）
    const refreshed = await _tryRefresh();
    if (refreshed) {
      return request<T>(path, options, true);
    }
    _onUnauthorized?.();
    throw new ApiError({
      code: "AUTH_REQUIRED",
      message: "認証が必要です。再度ログインしてください。",
      action: "ログインし直してください",
    });
  }

  if (response.status === 401) {
    _onUnauthorized?.();
    throw new ApiError({
      code: "AUTH_REQUIRED",
      message: "認証が必要です。再度ログインしてください。",
      action: "ログインし直してください",
    });
  }

  if (!response.ok) {
    const body = await getErrorBody(response);
    const fallbackMessage =
      response.status >= 500
        ? "サーバーエラーが発生しました。しばらくしてから再度お試しください。"
        : "リクエストの処理に失敗しました。";
    const apiError = buildApiError(response, body, fallbackMessage);

    if (apiError.code === "AUTH_EXPIRED" || apiError.code === "AUTH_REQUIRED") {
      _onUnauthorized?.();
    }

    throw apiError;
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

export { API_BASE_URL };
