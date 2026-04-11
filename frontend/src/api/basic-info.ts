import type { BasicInfoPayload, BasicInfoResponse } from "../types";
import { request } from "./client";

export const BASIC_INFO_REQUIRED_MESSAGE = "基本情報の氏名と記載日を先に登録してください。";

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

export async function assertBasicInfoReady(): Promise<void> {
  try {
    const basicInfo = await getLatestBasicInfo();
    if (!basicInfo.full_name || !basicInfo.record_date) {
      throw new Error(BASIC_INFO_REQUIRED_MESSAGE);
    }
  } catch (error) {
    if (error instanceof Error && error.message === BASIC_INFO_REQUIRED_MESSAGE) {
      throw error;
    }
    throw new Error(BASIC_INFO_REQUIRED_MESSAGE);
  }
}
