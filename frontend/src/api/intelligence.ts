import { request } from "./client";

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

export interface SkillTimelinePoint {
  period: string;
  activity: number; // 重み付きアクティビティ（float）
}

export interface SkillActivityItem {
  skill: string;
  timeline: SkillTimelinePoint[];
}

export interface SkillActivityResponse {
  skills: SkillActivityItem[];
}

export interface PositionAdviceResponse {
  advice: string;
  available: boolean;
}

export interface CachedAnalysisResponse {
  analysis_result: AnalysisResponse | null;
  position_advice: string | null;
  skill_activity_month: SkillActivityItem[] | null;
  skill_activity_year: SkillActivityItem[] | null;
}

/**
 * GitHub プロフィールの分析を開始します。
 */
export function analyzeGitHub(payload: AnalyzeGitHubPayload): Promise<AnalysisResponse> {
  return request<AnalysisResponse>("/api/intelligence/analyze", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

/**
 * スキルアクティビティ（時系列集計）を取得します。
 */
export function getSkillActivity(interval: "month" | "year" = "month"): Promise<SkillActivityResponse> {
  return request<SkillActivityResponse>(`/api/intelligence/skill-activity?interval=${interval}`, {
    method: "POST",
  });
}

/**
 * ポジションスコアに基づく現状分析+学習アドバイスを取得します。
 */
export function getPositionAdvice(): Promise<PositionAdviceResponse> {
  return request<PositionAdviceResponse>("/api/intelligence/position-advice", {
    method: "POST",
  });
}

/**
 * DB に保存された分析キャッシュを取得します。
 */
export function getAnalysisCache(): Promise<CachedAnalysisResponse> {
  return request<CachedAnalysisResponse>("/api/intelligence/cache");
}
