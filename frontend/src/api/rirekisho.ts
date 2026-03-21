import type { ResumePayload, ResumeResponse } from "../types";
import { request } from "./client";
import { downloadBlob, getBlobUrl } from "./download";

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

export function downloadResumePdf(id: string): Promise<void> {
  return downloadBlob(`/api/rirekisho/${id}/pdf`, `Resume-${id}.pdf`);
}

export function downloadResumeMarkdown(id: string): Promise<void> {
  return downloadBlob(`/api/rirekisho/${id}/markdown`, `rirekisho-${id}.md`);
}

export function getResumePdfBlobUrl(id: string): Promise<string> {
  return getBlobUrl(`/api/rirekisho/${id}/pdf`);
}
