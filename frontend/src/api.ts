import type { ResumePayload, ResumeResponse } from "./types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers ?? {})
    },
    ...options
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || "API request failed");
  }

  return (await response.json()) as T;
}

export function createResume(payload: ResumePayload): Promise<ResumeResponse> {
  return request<ResumeResponse>("/api/resumes", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function updateResume(id: string, payload: ResumePayload): Promise<ResumeResponse> {
  return request<ResumeResponse>(`/api/resumes/${id}`, {
    method: "PUT",
    body: JSON.stringify(payload)
  });
}

export async function downloadResumePdf(id: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/resumes/${id}/pdf`);
  if (!response.ok) {
    throw new Error("PDFのダウンロードに失敗しました");
  }

  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `resume-${id}.pdf`;
  anchor.click();
  URL.revokeObjectURL(url);
}
