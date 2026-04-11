"""技術スタックのマージロジック（決定的・LLM非依存）。

複数のソース（Resume / GitHub 分析 / 資格）から技術スタックを収集し、
優先度付きテキストにマージする。
"""

from ...models import BasicInfo, GitHubAnalysisCache, Resume


def collect_resume_tech_stacks(resume: Resume) -> set[str]:
    """Resume のプロジェクト技術スタックから技術名を収集する。"""
    techs: set[str] = set()
    for exp in resume.experiences:
        for client in exp.clients:
            for proj in client.projects:
                for st in proj.technology_stacks:
                    techs.add(st.name)
    return techs


def collect_github_skills(analysis_cache: GitHubAnalysisCache | None) -> set[str]:
    """GitHub 分析キャッシュからスキル一覧を収集する。"""
    if not analysis_cache or not analysis_cache.analysis_result:
        return set()
    ar = analysis_cache.analysis_result
    skills: set[str] = set()
    for repo in ar.get("repositories", []):
        for s in repo.get("skills", []):
            skills.add(s)
    return skills


def collect_qualification_names(basic_info: BasicInfo | None) -> set[str]:
    """BasicInfo の資格名を収集する。"""
    if not basic_info:
        return set()
    return {q.name for q in basic_info.qualifications}


def merge_tech_stacks(
    resume_techs: set[str],
    github_skills: set[str],
    qualification_names: set[str],
) -> str:
    """3ソースをマージして優先度付きリストをテキストで返す。

    優先度:
        1. 案件実績（Resume）
        2. 個人開発（GitHub）
        3. 資格のみ
    """
    parts: list[str] = []

    p1 = sorted(resume_techs)
    if p1:
        parts.append(f"優先度1（案件実績）: {', '.join(p1)}")

    p2 = sorted(github_skills - resume_techs)
    if p2:
        parts.append(f"優先度2（個人開発）: {', '.join(p2)}")

    p3 = sorted(qualification_names - resume_techs - github_skills)
    if p3:
        parts.append(f"優先度3（資格のみ）: {', '.join(p3)}")

    return "\n".join(parts) if parts else "（技術スタック情報なし）"
