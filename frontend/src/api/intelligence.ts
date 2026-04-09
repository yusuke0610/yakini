import { request } from "./client";
import type { TaskStatusResponse } from "./career-analysis";

export interface AnalyzeGitHubPayload {
  include_forks?: boolean;
}

export interface PositionScores {
  backend: number;
  frontend: number;
  fullstack: number;
  sre: number;
  cloud: number;
  missing_skills: string[];
}

export interface AnalysisResponse {
  username: string;
  repos_analyzed: number;
  unique_skills: number;
  analyzed_at: string;
  languages: Record<string, number>;
  position_scores: PositionScores | null;
}

export interface CachedAnalysisResponse {
  analysis_result: AnalysisResponse | null;
  position_advice: string | null;
  status?: string;
  error_message?: string;
  error_code?: string;
}

/**
 * GitHub プロフィールの分析を開始します（202 非同期）。
 */
export function analyzeGitHub(payload: AnalyzeGitHubPayload): Promise<{ status: string }> {
  return request<{ status: string }>("/api/intelligence/analyze", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

/**
 * DB に保存された分析キャッシュを取得します。
 */
export function getAnalysisCache(): Promise<CachedAnalysisResponse> {
  return request<CachedAnalysisResponse>("/api/intelligence/cache");
}

/**
 * 分析ステータスを取得します（ポーリング用）。
 */
export function getAnalysisCacheStatus(): Promise<TaskStatusResponse> {
  return request<TaskStatusResponse>("/api/intelligence/cache/status");
}
