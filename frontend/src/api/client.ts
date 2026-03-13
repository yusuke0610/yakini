const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

let _authToken: string | null = null;
let _onUnauthorized: (() => void) | null = null;

export function setAuthToken(token: string | null): void {
  _authToken = token;
}

export function setOnUnauthorized(callback: () => void): void {
  _onUnauthorized = callback;
}

export function getAuthHeaders(): Record<string, string> {
  const headers: Record<string, string> = {};
  if (_authToken) {
    headers["Authorization"] = `Bearer ${_authToken}`;
  }
  return headers;
}

export async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...((options.headers as Record<string, string>) ?? {}),
  };
  if (_authToken) {
    headers["Authorization"] = `Bearer ${_authToken}`;
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    _onUnauthorized?.();
    throw new Error("認証が必要です。再度ログインしてください。");
  }

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || "API request failed");
  }

  return (await response.json()) as T;
}

export { API_BASE_URL };
