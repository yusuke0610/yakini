"""LLM を利用したキャリア分析・ブログ記事の要約生成。

システムプロンプトは backend/prompts/ 配下の MD ファイルから都度読み込む。
"""

import logging
from typing import Any, Dict, List

from ...utils.prompt_loader import load_prompt
from .llm import get_llm_client

logger = logging.getLogger(__name__)

_client = get_llm_client()


async def check_llm_available() -> bool:
    """LLM バックエンドが利用可能か確認します。"""
    return await _client.check_available()


def _build_blog_prompt(articles: List[Dict[str, Any]]) -> str:
    """ブログ記事データから分析用プロンプトを構築する。"""
    parts = [f"記事数: {len(articles)}"]

    for i, art in enumerate(articles[:30], 1):
        line = f"{i}. {art.get('title', '')}"
        if art.get("tags"):
            line += f" [タグ: {', '.join(art['tags'])}]"
        if art.get("summary"):
            line += f" — {art['summary'][:100]}"
        if art.get("likes_count", 0) > 0:
            line += f" (いいね: {art['likes_count']})"
        parts.append(line)

    return "\n".join(parts)


async def summarize_blog_articles(articles: List[Dict[str, Any]]) -> str:
    """ブログ記事一覧から LLM で AI サマリを生成する。

    LLM に接続できない場合は空文字列を返す。
    """
    system_prompt = load_prompt("blog_analysis.md")
    prompt = _build_blog_prompt(articles)
    return await _client.generate(system_prompt, prompt)


def _build_learning_advice_prompt(
    analysis: Dict[str, Any],
    scores: Dict[str, Any],
) -> str:
    """分析データとポジションスコアから統合プロンプトを構築する。"""
    parts = []

    # 基本情報
    parts.append(f"ユーザー: {analysis.get('username', 'N/A')}")
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


async def generate_learning_advice(
    analysis: Dict[str, Any],
    scores: Dict[str, Any],
) -> str:
    """分析結果とポジションスコアから現状分析+学習アドバイスを LLM で生成する。

    LLM に接続できない場合は空文字列を返す。
    """
    system_prompt = load_prompt("github_analysis.md")
    prompt = _build_learning_advice_prompt(analysis, scores)
    return await _client.generate(system_prompt, prompt)
