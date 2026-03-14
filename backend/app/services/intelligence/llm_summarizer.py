"""Ollama / Qwen2.5 integration for career analysis summarization."""

import logging
import os
from typing import Any, Dict

import httpx

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:7b")

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
    """Check if Ollama server is reachable."""
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            return resp.status_code == 200
    except (httpx.ConnectError, httpx.TimeoutException):
        return False


async def summarize_analysis(analysis: Dict[str, Any]) -> str:
    """Generate a natural language summary of the analysis using Ollama.

    Returns an empty string if Ollama is not available.
    """
    user_prompt = _build_user_prompt(analysis)

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
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
        logger.info("Ollama is not available at %s", OLLAMA_BASE_URL)
        return ""
    except Exception:
        logger.exception("Failed to generate summary via Ollama")
        return ""
