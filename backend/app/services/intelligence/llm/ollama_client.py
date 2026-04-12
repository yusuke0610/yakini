"""Ollama バックエンドクライアント。"""

import logging
import os
import time

import httpx

from .base import LLMClient

logger = logging.getLogger(__name__)


class OllamaClient(LLMClient):
    """Ollama API を使用した LLM クライアント。"""

    def __init__(self) -> None:
        self.base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model = os.environ.get("OLLAMA_MODEL", "gemma3:4b")
        self.timeout = float(os.environ.get("OLLAMA_TIMEOUT", "1200.0"))  # デフォルトは 20 分

    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Ollama API でテキスト生成を実行する。"""
        start = time.monotonic()
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "system": system_prompt,
                        "prompt": user_prompt,
                        "stream": False,
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                duration_ms = int((time.monotonic() - start) * 1000)
                logger.info(
                    "Ollama 生成完了",
                    extra={"status": "completed", "duration_ms": duration_ms},
                )
                return data.get("response", "").strip()
        except httpx.ConnectError:
            logger.info("Ollama が %s で利用できません", self.base_url)
            return ""
        except httpx.TimeoutException:
            duration_ms = int((time.monotonic() - start) * 1000)
            logger.warning(
                "Ollama 生成がタイムアウトしました (%.1f秒)",
                self.timeout,
                extra={
                    "status": "failed",
                    "error_type": "TimeoutException",
                    "duration_ms": duration_ms,
                },
            )
            return ""
        except Exception:
            duration_ms = int((time.monotonic() - start) * 1000)
            logger.exception(
                "Ollama による生成に失敗しました",
                extra={"status": "failed", "duration_ms": duration_ms},
            )
            return ""

    async def check_available(self) -> bool:
        """Ollama サーバーに接続可能、かつ指定モデルが利用可能か確認する。"""
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get(f"{self.base_url}/api/tags")
                if resp.status_code != 200:
                    return False
                models = [m.get("name", "") for m in resp.json().get("models", [])]
                return self.model in models
        except (httpx.ConnectError, httpx.TimeoutException):
            return False
