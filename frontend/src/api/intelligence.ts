import { request } from "./client";

export interface AnalyzeGitHubPayload {
  include_forks?: boolean;
}

export interface AnalysisResponse {
  username: string;
  repos_analyzed: number;
  unique_skills: number;
  analyzed_at: string;
  languages: Record<string, number>;
}

export interface SummarizeResponse {
  summary: string;
  available: boolean;
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

export interface CachedAnalysisResponse {
  analysis_result: AnalysisResponse | null;
  ai_summary: string | null;
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
 * 分析結果から AI 要約を生成します。
 */
export function summarizeAnalysis(analysis: AnalysisResponse): Promise<SummarizeResponse> {
  return request<SummarizeResponse>("/api/intelligence/summarize", {
    method: "POST",
    body: JSON.stringify({ analysis }),
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
 * DB に保存された分析キャッシュを取得します。
 */
export function getAnalysisCache(): Promise<CachedAnalysisResponse> {
  return request<CachedAnalysisResponse>("/api/intelligence/cache");
}
