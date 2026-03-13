import type { CareerResumePayload, CareerResumeResponse } from "../types";
import { request, getAuthHeaders, API_BASE_URL } from "./client";

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
  const response = await fetch(`${API_BASE_URL}/api/resumes/${id}/pdf`, {
    headers: getAuthHeaders(),
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
  const response = await fetch(`${API_BASE_URL}/api/resumes/${id}/markdown`, {
    headers: getAuthHeaders(),
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
  const response = await fetch(`${API_BASE_URL}/api/resumes/${id}/pdf`, {
    headers: getAuthHeaders(),
  });
  if (!response.ok) {
    throw new Error("職務経歴書PDFのプレビューに失敗しました");
  }
  const blob = await response.blob();
  return URL.createObjectURL(blob);
}
