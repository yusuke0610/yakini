import type { CareerResumePayload, CareerResumeResponse } from "../types";
import { request } from "./client";
import { downloadBlob, getBlobUrl } from "./download";
import { PATHS } from "./paths";

export function getLatestCareerResume(): Promise<CareerResumeResponse> {
  return request<CareerResumeResponse>(PATHS.resumes.latest);
}

export function createCareerResume(payload: CareerResumePayload): Promise<CareerResumeResponse> {
  return request<CareerResumeResponse>(PATHS.resumes.base, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateCareerResume(
  id: string,
  payload: CareerResumePayload,
): Promise<CareerResumeResponse> {
  return request<CareerResumeResponse>(PATHS.resumes.byId(id), {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export function deleteCareerResume(): Promise<{ message: string }> {
  return request<{ message: string }>(PATHS.resumes.base, { method: "DELETE" });
}

export function downloadCareerResumePdf(id: string): Promise<void> {
  return downloadBlob(PATHS.resumes.pdf(id), `career-resume-${id}.pdf`);
}

export function downloadCareerResumeMarkdown(id: string): Promise<void> {
  return downloadBlob(PATHS.resumes.markdown(id), `career-resume-${id}.md`);
}

export function getCareerResumePdfBlobUrl(id: string): Promise<string> {
  return getBlobUrl(PATHS.resumes.pdf(id));
}
