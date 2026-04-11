"""AI キャリアパス分析の生成エントリポイント。

tech_stack_merger / prompt_builder に委譲し、LLM 呼び出しとレスポンス解析を担う。
"""

import json
import logging

from sqlalchemy.orm import Session

from ...models import BlogSummaryCache, GitHubAnalysisCache, Resume
from ...services.intelligence.llm.base import LLMClient
from .prompt_builder import SYSTEM_PROMPT, build_user_prompt
from .tech_stack_merger import (
    collect_github_skills,
    collect_qualification_names,
    collect_resume_tech_stacks,
    merge_tech_stacks,
)

logger = logging.getLogger(__name__)


def _parse_llm_response(raw: str) -> dict:
    """LLM レスポンスの JSON をパースしてバリデーションする。"""
    text = raw.strip()
    # コードブロックが含まれている場合は除去
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [ln for ln in lines if not ln.strip().startswith("```")]
        text = "\n".join(lines)

    data = json.loads(text)

    # 必須キーの存在チェック
    required = ["growth_summary", "tech_stack", "strengths", "career_paths", "action_items"]
    for key in required:
        if key not in data:
            raise ValueError(f"必須キー '{key}' が応答に含まれていません")

    # career_paths が 3件あることの確認
    paths = data.get("career_paths", [])
    if len(paths) < 3:
        # 不足分をダミーで補完
        horizons = ["short", "mid", "long"]
        labels = ["1年以内", "3年以内", "5年以内"]
        existing = {p.get("horizon") for p in paths}
        for h, lbl in zip(horizons, labels):
            if h not in existing:
                paths.append({
                    "horizon": h, "label": lbl, "title": "（提案なし）",
                    "description": "", "required_skills": [], "gap_skills": [], "fit_score": 0,
                })
        data["career_paths"] = paths[:3]

    # fit_score のクランプ処理
    for path in data["career_paths"]:
        score = path.get("fit_score", 0)
        if isinstance(score, (int, float)):
            path["fit_score"] = max(0, min(100, int(score)))
        else:
            path["fit_score"] = 0

    return data


async def build_career_analysis(
    db: Session,
    user_id: str,
    target_position: str,
    llm_client: LLMClient,
) -> dict:
    """AI キャリアパス分析を実行し、CareerAnalysisResult 構造の dict を返す。

    Raises:
        ValueError: LLM レスポンスのパースに失敗した場合。
    """
    # 入力データ収集
    resume = db.query(Resume).filter_by(user_id=user_id).first()
    analysis_cache = db.query(GitHubAnalysisCache).filter_by(user_id=user_id).first()
    blog_cache = db.query(BlogSummaryCache).filter_by(user_id=user_id).first()

    # 3ソースの技術スタックをマージ
    resume_techs = collect_resume_tech_stacks(resume) if resume else set()
    github_skills = collect_github_skills(analysis_cache)
    qualification_names = collect_qualification_names(resume)
    merged_stacks_text = merge_tech_stacks(resume_techs, github_skills, qualification_names)

    # プロンプト組み立て（氏名は渡さない・企業名はマスキング）
    user_prompt = build_user_prompt(
        target_position, resume, analysis_cache, blog_cache, merged_stacks_text,
    )

    # LLM 呼び出し
    raw_response = await llm_client.generate(SYSTEM_PROMPT, user_prompt)
    if not raw_response:
        raise ValueError("LLM からの応答が空です")

    # パースとバリデーション
    try:
        result = _parse_llm_response(raw_response)
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        logger.error("LLM レスポンスのパースに失敗: %s", exc)
        raise ValueError("LLM レスポンスの解析に失敗しました") from exc

    return result
