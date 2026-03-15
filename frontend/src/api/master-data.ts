import type { MasterItem, TechStackMasterItem } from "../types";
import { request } from "./client";

export function getQualifications(): Promise<MasterItem[]> {
  return request<MasterItem[]>("/api/master-data/qualification");
}

export function getTechnologyStacks(): Promise<TechStackMasterItem[]> {
  return request<TechStackMasterItem[]>("/api/master-data/technology-stack");
}

export function getPrefectures(): Promise<MasterItem[]> {
  return request<MasterItem[]>("/api/master-data/prefecture");
}
