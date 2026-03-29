import { request } from "./client";

/* ── 型定義 ──────────────────────────────────────────── */

export type EvidenceSource = "resume" | "github" | "blog" | "basic_info";
export type Horizon = "short" | "mid" | "long";

export interface TechStackItem {
  name: string;
  priority: 1 | 2 | 3;
  source: string;
  note?: string;
}

export interface StrengthItem {
  title: string;
  detail: string;
  evidence_source: EvidenceSource;
}

export interface CareerPathItem {
  horizon: Horizon;
  label: string;
  title: string;
  description: string;
  required_skills: string[];
  gap_skills: string[];
  fit_score: number;
}

export interface ActionItem {
  priority: number;
  action: string;
  reason: string;
}

export interface CareerAnalysisResult {
  growth_summary: string;
  tech_stack: { top: TechStackItem[]; summary: string };
  strengths: StrengthItem[];
  career_paths: CareerPathItem[];
  action_items: ActionItem[];
}

export interface CareerAnalysisResponse {
  id: number;
  version: number;
  target_position: string;
  result: CareerAnalysisResult;
  created_at: string;
}

/* ── API 関数 ─────────────────────────────────────────── */

/** キャリアパス分析を実行する。 */
export function generateAnalysis(targetPosition: string): Promise<CareerAnalysisResponse> {
  return request<CareerAnalysisResponse>("/api/career-analysis/generate", {
    method: "POST",
    body: JSON.stringify({ target_position: targetPosition }),
  });
}

/** 全分析結果を取得する。 */
export function listAnalyses(): Promise<CareerAnalysisResponse[]> {
  return request<CareerAnalysisResponse[]>("/api/career-analysis/");
}

/** 指定 ID の分析結果を取得する。 */
export function getAnalysis(id: number): Promise<CareerAnalysisResponse> {
  return request<CareerAnalysisResponse>(`/api/career-analysis/${id}`);
}

/** 分析結果を削除する。 */
export function deleteAnalysis(id: number): Promise<void> {
  return request<void>(`/api/career-analysis/${id}`, {
    method: "DELETE",
  });
}
