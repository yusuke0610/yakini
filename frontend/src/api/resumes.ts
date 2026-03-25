import type { CareerResumePayload, CareerResumeResponse } from "../types";
import { request } from "./client";
import { downloadBlob, getBlobUrl } from "./download";

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

export function deleteCareerResume(): Promise<{ message: string }> {
  return request<{ message: string }>("/api/resumes", { method: "DELETE" });
}

export function downloadCareerResumePdf(id: string): Promise<void> {
  return downloadBlob(`/api/resumes/${id}/pdf`, `career-resume-${id}.pdf`);
}

export function downloadCareerResumeMarkdown(id: string): Promise<void> {
  return downloadBlob(`/api/resumes/${id}/markdown`, `career-resume-${id}.md`);
}

export function getCareerResumePdfBlobUrl(id: string): Promise<string> {
  return getBlobUrl(`/api/resumes/${id}/pdf`);
}
