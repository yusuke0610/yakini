import type { MasterDataItem } from "../types";
import { request } from "./client";

export function getMasterData(category: string): Promise<MasterDataItem[]> {
  return request<MasterDataItem[]>(`/api/master-data/${category}`);
}
