import { API_BASE_URL, getAuthHeaders } from "./client";

export async function downloadBlob(
  url: string,
  filename: string,
  options?: RequestInit,
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}${url}`, {
    ...options,
    headers: {
      ...getAuthHeaders(),
      ...((options?.headers as Record<string, string>) ?? {}),
    },
  });
  if (!response.ok) {
    throw new Error(`ダウンロードに失敗しました: ${filename}`);
  }
  const blob = await response.blob();
  const blobUrl = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = blobUrl;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(blobUrl);
}

export async function getBlobUrl(url: string): Promise<string> {
  const response = await fetch(`${API_BASE_URL}${url}`, {
    headers: getAuthHeaders(),
  });
  if (!response.ok) {
    throw new Error("プレビューの取得に失敗しました");
  }
  const blob = await response.blob();
  return URL.createObjectURL(blob);
}
