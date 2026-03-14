import { request } from "./client";
import { downloadBlob } from "./download";

export interface AnalyzeGitHubPayload {
  include_forks?: boolean;
}

export interface AnalysisResponse {
  username: string;
  repos_analyzed: number;
  unique_skills: number;
  analyzed_at: string;
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
 * 分析結果を PDF としてダウンロードします。
 */
export function downloadAnalysisPdf(
  analysis: AnalysisResponse,
  summary?: string | null,
): Promise<void> {
  return downloadBlob(
    "/api/intelligence/download/pdf",
    `github-analysis-${analysis.username}.pdf`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ analysis, summary: summary ?? null }),
    },
  );
}

/**
 * 分析結果を Markdown としてダウンロードします。
 */
export function downloadAnalysisMarkdown(
  analysis: AnalysisResponse,
  summary?: string | null,
): Promise<void> {
  return downloadBlob(
    "/api/intelligence/download/markdown",
    `github-analysis-${analysis.username}.md`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ analysis, summary: summary ?? null }),
    },
  );
}

/**
 * スキルアクティビティ（時系列集計）を取得します。
 */
export function getSkillActivity(interval: "month" | "year" = "month"): Promise<SkillActivityResponse> {
  return request<SkillActivityResponse>(`/api/intelligence/skill-activity?interval=${interval}`, {
    method: "POST",
  });
}
