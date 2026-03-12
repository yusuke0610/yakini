import type {
  BasicInfoPayload,
  BasicInfoResponse,
  CareerResumePayload,
  CareerResumeResponse,
  ResumePayload,
  ResumeResponse,
} from "./types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

let _authToken: string | null = null;
let _onUnauthorized: (() => void) | null = null;

export function setAuthToken(token: string | null): void {
  _authToken = token;
}

export function setOnUnauthorized(callback: () => void): void {
  _onUnauthorized = callback;
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
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

export function login(
  username: string,
  password: string,
): Promise<{ access_token: string; token_type: string }> {
  return request("/auth/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
}

export function register(
  username: string,
  email: string,
  password: string,
): Promise<{ access_token: string; token_type: string }> {
  return request("/auth/register", {
    method: "POST",
    body: JSON.stringify({ username, email, password }),
  });
}

export function getGitHubOAuthUrl(): string {
  const clientId = import.meta.env.VITE_GITHUB_CLIENT_ID ?? "";
  const redirectUri = `${window.location.origin}/`;
  return `https://github.com/login/oauth/authorize?client_id=${clientId}&redirect_uri=${encodeURIComponent(redirectUri)}&scope=read:user`;
}

export function githubCallback(
  code: string,
): Promise<{ access_token: string; token_type: string }> {
  return request("/auth/github/callback", {
    method: "POST",
    body: JSON.stringify({ code }),
  });
}

export function createBasicInfo(payload: BasicInfoPayload): Promise<BasicInfoResponse> {
  return request<BasicInfoResponse>("/api/basic-info", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateBasicInfo(id: string, payload: BasicInfoPayload): Promise<BasicInfoResponse> {
  return request<BasicInfoResponse>(`/api/basic-info/${id}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export function getLatestBasicInfo(): Promise<BasicInfoResponse> {
  return request<BasicInfoResponse>("/api/basic-info/latest");
}

export function getLatestCareerResume(): Promise<CareerResumeResponse> {
  return request<CareerResumeResponse>("/api/resumes/latest");
}

export function createCareerResume(payload: CareerResumePayload): Promise<CareerResumeResponse> {
  return request<CareerResumeResponse>("/api/resumes", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateCareerResume(
  id: string,
  payload: CareerResumePayload,
): Promise<CareerResumeResponse> {
  return request<CareerResumeResponse>(`/api/resumes/${id}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export async function downloadCareerResumePdf(id: string): Promise<void> {
  const headers: Record<string, string> = {};
  if (_authToken) {
    headers["Authorization"] = `Bearer ${_authToken}`;
  }
  const response = await fetch(`${API_BASE_URL}/api/resumes/${id}/pdf`, {
    headers,
  });
  if (!response.ok) {
    throw new Error("職務経歴書PDFのダウンロードに失敗しました");
  }

  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `career-resume-${id}.pdf`;
  anchor.click();
  URL.revokeObjectURL(url);
}

export async function downloadCareerResumeMarkdown(id: string): Promise<void> {
  const headers: Record<string, string> = {};
  if (_authToken) {
    headers["Authorization"] = `Bearer ${_authToken}`;
  }
  const response = await fetch(`${API_BASE_URL}/api/resumes/${id}/markdown`, {
    headers,
  });
  if (!response.ok) {
    throw new Error("職務経歴書Markdownのダウンロードに失敗しました");
  }

  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `career-resume-${id}.md`;
  anchor.click();
  URL.revokeObjectURL(url);
}

export async function getCareerResumePdfBlobUrl(id: string): Promise<string> {
  const headers: Record<string, string> = {};
  if (_authToken) {
    headers["Authorization"] = `Bearer ${_authToken}`;
  }
  const response = await fetch(`${API_BASE_URL}/api/resumes/${id}/pdf`, {
    headers,
  });
  if (!response.ok) {
    throw new Error("職務経歴書PDFのプレビューに失敗しました");
  }
  const blob = await response.blob();
  return URL.createObjectURL(blob);
}

export function getLatestResume(): Promise<ResumeResponse> {
  return request<ResumeResponse>("/api/rirekisho/latest");
}

export function createResume(payload: ResumePayload): Promise<ResumeResponse> {
  return request<ResumeResponse>("/api/rirekisho", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateResume(id: string, payload: ResumePayload): Promise<ResumeResponse> {
  return request<ResumeResponse>(`/api/rirekisho/${id}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export async function downloadResumePdf(id: string): Promise<void> {
  const headers: Record<string, string> = {};
  if (_authToken) {
    headers["Authorization"] = `Bearer ${_authToken}`;
  }
  const response = await fetch(`${API_BASE_URL}/api/rirekisho/${id}/pdf`, {
    headers,
  });
  if (!response.ok) {
    throw new Error("履歴書PDFのダウンロードに失敗しました");
  }

  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `Resume-${id}.pdf`;
  anchor.click();
  URL.revokeObjectURL(url);
}

export async function downloadResumeMarkdown(id: string): Promise<void> {
  const headers: Record<string, string> = {};
  if (_authToken) {
    headers["Authorization"] = `Bearer ${_authToken}`;
  }
  const response = await fetch(`${API_BASE_URL}/api/rirekisho/${id}/markdown`, {
    headers,
  });
  if (!response.ok) {
    throw new Error("履歴書Markdownのダウンロードに失敗しました");
  }

  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `rirekisho-${id}.md`;
  anchor.click();
  URL.revokeObjectURL(url);
}

export async function getResumePdfBlobUrl(id: string): Promise<string> {
  const headers: Record<string, string> = {};
  if (_authToken) {
    headers["Authorization"] = `Bearer ${_authToken}`;
  }
  const response = await fetch(`${API_BASE_URL}/api/rirekisho/${id}/pdf`, {
    headers,
  });
  if (!response.ok) {
    throw new Error("履歴書PDFのプレビューに失敗しました");
  }
  const blob = await response.blob();
  return URL.createObjectURL(blob);
}
