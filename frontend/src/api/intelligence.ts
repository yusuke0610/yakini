import { request } from "./client";
import { downloadBlob } from "./download";

export interface AnalyzeGitHubPayload {
  include_forks?: boolean;
}

export interface AnalysisResponse {
  username: string;
  repos_analyzed: number;
  unique_skills: number;
  timelines: Array<{
    skill_name: string;
    category: string;
    first_seen: string;
    last_seen: string;
    usage_frequency: number;
    repositories: string[];
    yearly_usage: Record<string, number>;
  }>;
  year_snapshots: Array<{
    year: string;
    skills: string[];
    new_skills: string[];
  }>;
  growth: Array<{
    skill_name: string;
    category: string;
    trend: string;
    velocity: number;
    yearly_usage: Record<string, number>;
    first_seen: string;
    last_seen: string;
    total_repos: number;
  }>;
  prediction: {
    current_role: {
      role_name: string;
      confidence: number;
      matching_skills: string[];
      missing_skills: string[];
      seniority: number;
    };
    next_roles: Array<{
      role_name: string;
      confidence: number;
      matching_skills: string[];
      missing_skills: string[];
      seniority: number;
    }>;
    long_term_roles: Array<{
      role_name: string;
      confidence: number;
      matching_skills: string[];
      missing_skills: string[];
      seniority: number;
    }>;
    skill_summary: Record<string, string[]>;
  };
  simulation: {
    current_role: string;
    paths: Array<{
      path: string[];
      confidence: number;
      description: string;
    }>;
    total_paths_explored: number;
  };
  analyzed_at: string;
}

export interface SummarizeResponse {
  summary: string;
  available: boolean;
}

export function analyzeGitHub(payload: AnalyzeGitHubPayload): Promise<AnalysisResponse> {
  return request<AnalysisResponse>("/api/intelligence/analyze", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function summarizeAnalysis(analysis: AnalysisResponse): Promise<SummarizeResponse> {
  return request<SummarizeResponse>("/api/intelligence/summarize", {
    method: "POST",
    body: JSON.stringify({ analysis }),
  });
}

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
