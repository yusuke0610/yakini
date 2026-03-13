import type { ResumePayload, ResumeResponse } from "../types";
import { request, getAuthHeaders, API_BASE_URL } from "./client";

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
  const response = await fetch(`${API_BASE_URL}/api/rirekisho/${id}/pdf`, {
    headers: getAuthHeaders(),
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
  const response = await fetch(`${API_BASE_URL}/api/rirekisho/${id}/markdown`, {
    headers: getAuthHeaders(),
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
  const response = await fetch(`${API_BASE_URL}/api/rirekisho/${id}/pdf`, {
    headers: getAuthHeaders(),
  });
  if (!response.ok) {
    throw new Error("履歴書PDFのプレビューに失敗しました");
  }
  const blob = await response.blob();
  return URL.createObjectURL(blob);
}
