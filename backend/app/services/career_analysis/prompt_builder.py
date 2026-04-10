"""AI キャリアパス分析 LLM プロンプト構築ロジック。

SYSTEM_PROMPT と _build_user_prompt を提供する。
LLM 呼び出し自体は builder.py が担う。
"""

from ...models import BasicInfo, BlogSummaryCache, GitHubAnalysisCache, Resume, Rirekisho

SYSTEM_PROMPT = """あなたは日本の IT エンジニアのキャリア支援を専門とするアドバイザーです。
提供されたエンジニアの本業経験・個人活動・資格情報を総合的に分析し、
キャリアパス提案レポートを JSON 形式で返してください。

## 分析の指針

### 成長曲線の評価
- IT 業界入社以降の経歴のみを対象とする
- 担当フェーズの変化（実装 → 設計 → アーキテクチャなど）
- 技術スタックの深化・多様化の軌跡
- 本業と個人活動（GitHub・ブログ）が示す「仕事外での自己投資」の評価

### 技術スタック評価の優先順位（必ず守ること）
1. 案件で実績を上げたもの（最も高く評価する）
2. 個人開発で使用しているもの（2番目に評価する）
3. 資格で取得しているもの（3番目）
※ 同一技術が複数ソースに存在する場合は最も高い優先度で評価する

### キャリアパス提案
- 短期（1年以内）・中期（3年以内）・長期（5年以内）の 3 段階で提案
- 現在のスキルセット・ターゲットポジションを踏まえた具体的なアクションを含める
- ギャップスキルは「なぜそのスキルが必要か」を明示する
- fit_score は現在地からそのパスへの到達しやすさ（0〜100）

### ルール
- 事実の捏造・誇張は行わない
- 本業と個人活動を明確に区別して言及する
- 出力は下記 JSON スキーマのみを返す（コードブロック・前置き不要）

出力 JSON スキーマ:
{
  "growth_summary": "IT 業界入社以降の成長曲線の総括テキスト（500〜800字程度）",
  "tech_stack": {
    "top": [
      {"name": "技術名", "priority": 1, "source": "案件実績", "note": "補足"}
    ],
    "summary": "技術スタック全体の評価コメント（200字程度）"
  },
  "strengths": [
    {"title": "強みタイトル", "detail": "根拠エピソード", "evidence_source": "resume|github|blog|basic_info"}
  ],
  "career_paths": [
    {"horizon": "short", "label": "1年以内", "title": "...", "description": "...", "required_skills": [], "gap_skills": [], "fit_score": 82},
    {"horizon": "mid", "label": "3年以内", "title": "...", "description": "...", "required_skills": [], "gap_skills": [], "fit_score": 68},
    {"horizon": "long", "label": "5年以内", "title": "...", "description": "...", "required_skills": [], "gap_skills": [], "fit_score": 55}
  ],
  "action_items": [
    {"priority": 1, "action": "具体的なアクション", "reason": "理由"}
  ]
}"""


def build_user_prompt(
    target_position: str,
    basic_info: BasicInfo | None,
    resume: Resume | None,
    rirekisho: Rirekisho | None,
    analysis_cache: GitHubAnalysisCache | None,
    blog_cache: BlogSummaryCache | None,
    merged_stacks_text: str,
) -> str:
    """ユーザープロンプトを動的に組み立てる。"""
    parts: list[str] = []

    parts.append(f"## ターゲットポジション\n{target_position}")

    # 基本情報 — 資格
    parts.append("\n## 基本情報")
    if basic_info and basic_info.qualifications:
        quals = [f"- {q.name}（{q.acquired_date}）" for q in basic_info.qualifications]
        parts.append("資格:\n" + "\n".join(quals))
    else:
        parts.append("資格: なし")

    # 職務経歴
    parts.append("\n## 職務経歴（本業・IT 業界入社以降）")

    if resume:
        if resume.career_summary:
            parts.append(f"\n### 職務要約\n{resume.career_summary}")

        parts.append("\n### 担当プロジェクト一覧")
        for exp in resume.experiences:
            for client in exp.clients:
                for proj in client.projects:
                    end = proj.end_date or "現在"
                    phases = ", ".join(proj.phases) if proj.phases else "不明"
                    stacks = ", ".join(st.name for st in proj.technology_stacks)
                    parts.append(f"- 案件名: {proj.name}")
                    parts.append(f"  期間: {proj.start_date} 〜 {end}")
                    parts.append(f"  担当フェーズ: {phases}")
                    parts.append(f"  使用技術: {stacks}")
                    if proj.description:
                        parts.append(f"  概要: {proj.description}")
    else:
        parts.append("（職務経歴書未入力）")

    # 技術スタック（マージ済み）
    parts.append(f"\n### 技術スタック（マージ済み・優先度付き）\n{merged_stacks_text}")

    # 履歴書（IT 業界入社以降の職歴のみ）
    if rirekisho and rirekisho.work_histories:
        parts.append("\n## IT 業界入社以降の職歴サマリ（履歴書より）")
        for wh in rirekisho.work_histories:
            parts.append(f"- {wh.name} / {wh.date}")

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
        parts.append(f"\n## ブログ発信力\n{blog_cache.summary}")

    parts.append(
        "\n---\n上記を踏まえて、指定の JSON スキーマでキャリアパス提案レポートを返してください。"
    )

    return "\n".join(parts)
