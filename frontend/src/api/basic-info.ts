import type { BasicInfoPayload, BasicInfoResponse } from "../types";
import { request } from "./client";

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
