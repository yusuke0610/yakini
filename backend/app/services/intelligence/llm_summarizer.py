"""Ollama / Qwen2.5 を利用したキャリア分析・ブログ記事の要約生成。"""

import logging
import os
from typing import Any, Dict, List

import httpx

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:7b")
OLLAMA_TIMEOUT = float(os.environ.get("OLLAMA_TIMEOUT", "180"))

SYSTEM_PROMPT = (
    "あなたはキャリア分析の専門家です。"
    "GitHubの活動データから得られた分析結果を基に、"
    "エンジニアのキャリアについて簡潔で洞察に満ちた日本語の要約を作成してください。"
    "要約は3〜5文程度で、以下の点に触れてください：\n"
    "1. 主要なスキルと技術的な強み\n"
    "2. スキルの成長傾向\n"
    "3. 現在のキャリアポジションと将来性\n"
    "箇条書きではなく自然な文章で書いてください。"
)


def _build_user_prompt(analysis: Dict[str, Any]) -> str:
    """分析データから簡潔なプロンプトを構築します。"""
    summary_parts = []

    summary_parts.append(f"ユーザー: {analysis.get('username', 'N/A')}")
    summary_parts.append(
        f"分析リポジトリ数: {analysis.get('repos_analyzed', 0)}"
    )
    summary_parts.append(
        f"ユニークスキル数: {analysis.get('unique_skills', 0)}"
    )

    # 成長トレンド（データがある場合のみ）
    growth = analysis.get("growth", [])
    if growth:
        emerging = [g["skill_name"] for g in growth if g.get("trend") == "emerging"]
        stable = [g["skill_name"] for g in growth if g.get("trend") == "stable"]
        declining = [g["skill_name"] for g in growth if g.get("trend") == "declining"]

        if emerging:
            summary_parts.append(f"成長中のスキル: {', '.join(emerging[:5])}")
        if stable:
            summary_parts.append(f"安定スキル: {', '.join(stable[:5])}")
        if declining:
            summary_parts.append(f"低下傾向: {', '.join(declining[:5])}")

    # 活動期間（データがある場合のみ）
    snapshots = analysis.get("year_snapshots", [])
    if snapshots:
        years = [s["year"] for s in snapshots]
        if years:
            summary_parts.append(f"活動期間: {min(years)} 〜 {max(years)}")

    return "\n".join(summary_parts)


async def check_ollama_available() -> bool:
    """Ollama サーバーに接続可能か確認します。"""
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            return resp.status_code == 200
    except (httpx.ConnectError, httpx.TimeoutException):
        return False


BLOG_SYSTEM_PROMPT = (
    "あなたはテックブログの分析専門家です。"
    "エンジニアのブログ記事一覧から、技術的な関心分野やアウトプット傾向を分析してください。"
    "要約は3〜5文程度で、以下の点に触れてください：\n"
    "1. 主要な技術的関心分野\n"
    "2. アウトプットの傾向（頻度、深さ、ジャンル）\n"
    "3. 技術的な強みや特徴\n"
    "箇条書きではなく自然な文章で書いてください。"
)


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
    """ブログ記事一覧から Ollama で AI サマリを生成する。

    Ollama に接続できない場合は空文字列を返す。
    """
    prompt = _build_blog_prompt(articles)

    try:
        async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT) as client:
            resp = await client.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": OLLAMA_MODEL,
                    "system": BLOG_SYSTEM_PROMPT,
                    "prompt": prompt,
                    "stream": False,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("response", "").strip()
    except (httpx.ConnectError, httpx.TimeoutException):
        logger.info("Ollama が %s で利用できません", OLLAMA_BASE_URL)
        return ""
    except Exception:
        logger.exception("ブログ記事の要約生成に失敗しました")
        return ""


async def summarize_analysis(analysis: Dict[str, Any]) -> str:
    """Ollama を使用して分析結果の自然言語要約を生成する。

    Ollama に接続できない場合は空文字列を返す。
    """
    user_prompt = _build_user_prompt(analysis)

    try:
        async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT) as client:
            resp = await client.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": OLLAMA_MODEL,
                    "system": SYSTEM_PROMPT,
                    "prompt": user_prompt,
                    "stream": False,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("response", "").strip()
    except (httpx.ConnectError, httpx.TimeoutException):
        logger.info("Ollama が %s で利用できません", OLLAMA_BASE_URL)
        return ""
    except Exception:
        logger.exception("Ollama による要約生成に失敗しました")
        return ""
