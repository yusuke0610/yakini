"""LLM を利用したキャリア分析・ブログ記事の要約生成。

システムプロンプトは backend/prompts/ 配下の MD ファイルから都度読み込む。
"""

from typing import Any, Dict, List, Optional

from ...core.logging_utils import get_logger
from ...core.metrics import measure_time_async
from ...utils.prompt_loader import load_prompt
from ..llm.sanitizer import SanitizeContext, sanitize_text
from .llm import get_llm_client

logger = get_logger(__name__)

_client = get_llm_client()


async def check_llm_available() -> bool:
    """LLM バックエンドが利用可能か確認します。"""
    return await _client.check_available()


def _build_blog_prompt(
    articles: List[Dict[str, Any]],
    context: Optional[SanitizeContext] = None,
) -> str:
    """ブログ記事データから分析用プロンプトを構築する。

    context が指定された場合、title と summary を sanitize_text() でマスキングする。
    未指定時は空コンテキストを使用する（マスキングなし）。
    """
    ctx = context if context is not None else SanitizeContext()
    parts = [f"記事数: {len(articles)}"]

    for i, art in enumerate(articles[:30], 1):
        title = sanitize_text(art.get("title", ""), ctx)
        line = f"{i}. {title}"
        if art.get("tags"):
            line += f" [タグ: {', '.join(art['tags'])}]"
        if art.get("summary"):
            summary = sanitize_text(art["summary"][:100], ctx)
            line += f" — {summary}"
        if art.get("likes_count", 0) > 0:
            line += f" (いいね: {art['likes_count']})"
        parts.append(line)

    return "\n".join(parts)


@measure_time_async("llm.blog_summarize")
async def summarize_blog_articles(
    articles: List[Dict[str, Any]],
    context: Optional[SanitizeContext] = None,
) -> str | None:
    """ブログ記事一覧から LLM で AI サマリを生成する。

    context が指定された場合、記事タイトル・要約を sanitize_text() でマスキングする。
    LLM に接続できない場合は None を返す。
    """
    system_prompt = load_prompt("blog_analysis.md")
    prompt = _build_blog_prompt(articles, context)
    return await _client.generate(system_prompt, prompt)


def _build_learning_advice_prompt(
    analysis: Dict[str, Any],
    scores: Dict[str, Any],
) -> str:
    """分析データとポジションスコアから統合プロンプトを構築する。

    username はプライバシー上 LLM に渡さない。
    """
    parts = []

    # username を除いた基本情報（A分類フィールドのみ）
    parts.append(f"分析リポジトリ数: {analysis.get('repos_analyzed', 0)}")
    parts.append(f"ユニークスキル数: {analysis.get('unique_skills', 0)}")

    # 言語情報
    languages = analysis.get("languages", {})
    if languages:
        total = sum(languages.values()) or 1
        sorted_langs = sorted(languages.items(), key=lambda x: x[1], reverse=True)[:10]
        lang_strs = [f"{name}: {b * 100 // total}%" for name, b in sorted_langs]
        parts.append(f"主要言語: {', '.join(lang_strs)}")

    # ポジションスコア
    parts.append("")
    parts.append("## 現在のポジションスコア")
    parts.append(f"Backend: {scores.get('backend', 0)}/100")
    parts.append(f"Frontend: {scores.get('frontend', 0)}/100")
    parts.append(f"Fullstack: {scores.get('fullstack', 0)}/100")
    parts.append(f"SRE: {scores.get('sre', 0)}/100")
    parts.append(f"Cloud: {scores.get('cloud', 0)}/100")

    # 不足スキル
    missing = scores.get("missing_skills", [])
    if missing:
        parts.append("\n## 不足しているスキル")
        for skill in missing:
            parts.append(f"- {skill}")
    else:
        parts.append("\n## 不足スキルなし（全要件を満たしています）")

    return "\n".join(parts)


@measure_time_async("llm.learning_advice")
async def generate_learning_advice(
    analysis: Dict[str, Any],
    scores: Dict[str, Any],
) -> str | None:
    """分析結果とポジションスコアから現状分析+学習アドバイスを LLM で生成する。

    LLM に接続できない場合は None を返す。
    """
    system_prompt = load_prompt("github_analysis.md")
    prompt = _build_learning_advice_prompt(analysis, scores)
    return await _client.generate(system_prompt, prompt)
