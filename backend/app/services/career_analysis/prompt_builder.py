"""AI キャリアパス分析 LLM プロンプト構築ロジック。

build_user_prompt を提供する。システムプロンプトは
backend/prompts/career_analysis.md から都度読み込む。
LLM 呼び出し自体は builder.py が担う。

PII（氏名・企業名）は LLM へ渡す前にマスキングする。
"""

from ...models import BlogSummaryCache, GitHubAnalysisCache, Resume


def _company_label(index: int) -> str:
    """0 起算インデックスから [企業A] [企業B] ... のラベルを生成する。"""
    return f"[企業{chr(ord('A') + index)}]" if index < 26 else f"[企業{index + 1}]"


def build_company_mask(resume: Resume | None) -> dict[str, str]:
    """Resume から登場する企業名を A, B, C... のラベルに対応付ける。

    所属企業（experiences.company）と取引先（clients.name）の両方をマスキング対象にする。
    """
    if not resume:
        return {}
    seen: dict[str, str] = {}
    for exp in resume.experiences:
        if exp.company and exp.company not in seen:
            seen[exp.company] = _company_label(len(seen))
        for client in exp.clients:
            if client.name and client.name not in seen:
                seen[client.name] = _company_label(len(seen))
    return seen


def mask_text(text: str, company_mask: dict[str, str]) -> str:
    """テキスト中の企業名をラベルに置換する。長い企業名から優先して置換する。"""
    if not text or not company_mask:
        return text or ""
    masked = text
    for name in sorted(company_mask.keys(), key=len, reverse=True):
        masked = masked.replace(name, company_mask[name])
    return masked


def build_user_prompt(
    target_position: str,
    resume: Resume | None,
    analysis_cache: GitHubAnalysisCache | None,
    blog_cache: BlogSummaryCache | None,
    merged_stacks_text: str,
) -> str:
    """ユーザープロンプトを動的に組み立てる。

    氏名は LLM に渡さない。企業名は [企業A] [企業B]... としてマスキングする。
    """
    parts: list[str] = []
    company_mask = build_company_mask(resume)

    parts.append(f"## ターゲットポジション\n{target_position}")

    # 資格
    parts.append("\n## 資格")
    if resume and resume.qualifications:
        quals = [f"- {q.name}（{q.acquired_date}）" for q in resume.qualifications]
        parts.append("\n".join(quals))
    else:
        parts.append("なし")

    # 職務経歴
    parts.append("\n## 職務経歴（本業・IT 業界入社以降）")

    if resume:
        if resume.career_summary:
            parts.append(f"\n### 職務要約\n{mask_text(resume.career_summary, company_mask)}")

        parts.append("\n### 担当プロジェクト一覧")
        for exp in resume.experiences:
            company_label = company_mask.get(exp.company, exp.company)
            for client in exp.clients:
                client_label = company_mask.get(client.name, client.name) if client.name else ""
                for proj in client.projects:
                    end = proj.end_date or "現在"
                    phases = ", ".join(proj.phases) if proj.phases else "不明"
                    stacks = ", ".join(st.name for st in proj.technology_stacks)
                    parts.append(f"- 案件名: {mask_text(proj.name, company_mask)}")
                    parts.append(f"  所属: {company_label}")
                    if client_label:
                        parts.append(f"  取引先: {client_label}")
                    parts.append(f"  期間: {proj.start_date} 〜 {end}")
                    parts.append(f"  担当フェーズ: {phases}")
                    parts.append(f"  使用技術: {stacks}")
                    if proj.description:
                        parts.append(f"  概要: {mask_text(proj.description, company_mask)}")
    else:
        parts.append("（職務経歴書未入力）")

    # 技術スタック（マージ済み）
    parts.append(f"\n### 技術スタック（マージ済み・優先度付き）\n{merged_stacks_text}")

    # GitHub 分析
    if analysis_cache and analysis_cache.analysis_result:
        ar = analysis_cache.analysis_result
        parts.append("\n## GitHub 個人活動")

        scores = ar.get("position_scores", {})
        if scores:
            parts.append(
                f"ポジションスコア: backend={scores.get('backend', 0)}, "
                f"frontend={scores.get('frontend', 0)}, "
                f"sre={scores.get('sre', 0)}, "
                f"cloud={scores.get('cloud', 0)}, "
                f"fullstack={scores.get('fullstack', 0)}"
            )
            missing = scores.get("missing_skills", [])
            if missing:
                parts.append(f"差分分析（不足スキル）: {', '.join(missing)}")

        languages = ar.get("languages", {})
        if languages:
            total = sum(languages.values()) or 1
            sorted_langs = sorted(languages.items(), key=lambda x: x[1], reverse=True)[:10]
            lang_strs = [f"{name}: {b * 100 // total}%" for name, b in sorted_langs]
            parts.append(f"主要言語: {', '.join(lang_strs)}")

        all_skills: set[str] = set()
        for repo in ar.get("repositories", []):
            for s in repo.get("skills", []):
                all_skills.add(s)
        if all_skills:
            parts.append(f"検出スキル: {', '.join(sorted(all_skills))}")

    # ブログ発信力
    if blog_cache and blog_cache.summary:
        parts.append(f"\n## ブログ発信力\n{mask_text(blog_cache.summary, company_mask)}")

    parts.append(
        "\n---\n上記を踏まえて、指定の JSON スキーマでキャリアパス提案レポートを返してください。"
    )

    return "\n".join(parts)
