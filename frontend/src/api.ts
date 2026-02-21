import type {
  BasicInfoPayload,
  BasicInfoResponse,
  CareerResumePayload,
  CareerResumeResponse,
  RirekishoPayload,
  RirekishoResponse
} from "./types";

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

export function createBasicInfo(payload: BasicInfoPayload): Promise<BasicInfoResponse> {
  return request<BasicInfoResponse>("/api/basic-info", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function updateBasicInfo(id: string, payload: BasicInfoPayload): Promise<BasicInfoResponse> {
  return request<BasicInfoResponse>(`/api/basic-info/${id}`, {
    method: "PUT",
    body: JSON.stringify(payload)
  });
}

export function getLatestBasicInfo(): Promise<BasicInfoResponse> {
  return request<BasicInfoResponse>("/api/basic-info/latest");
}

export function createCareerResume(payload: CareerResumePayload): Promise<CareerResumeResponse> {
  return request<CareerResumeResponse>("/api/resumes", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function updateCareerResume(
  id: string,
  payload: CareerResumePayload
): Promise<CareerResumeResponse> {
  return request<CareerResumeResponse>(`/api/resumes/${id}`, {
    method: "PUT",
    body: JSON.stringify(payload)
  });
}

export async function downloadCareerResumePdf(id: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/resumes/${id}/pdf`);
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

export function createRirekisho(payload: RirekishoPayload): Promise<RirekishoResponse> {
  return request<RirekishoResponse>("/api/rirekisho", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function updateRirekisho(id: string, payload: RirekishoPayload): Promise<RirekishoResponse> {
  return request<RirekishoResponse>(`/api/rirekisho/${id}`, {
    method: "PUT",
    body: JSON.stringify(payload)
  });
}

export async function downloadRirekishoPdf(id: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/rirekisho/${id}/pdf`);
  if (!response.ok) {
    throw new Error("履歴書PDFのダウンロードに失敗しました");
  }

  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `rirekisho-${id}.pdf`;
  anchor.click();
  URL.revokeObjectURL(url);
}
