"""Vertex AI Gemini バックエンドクライアント（google-genai SDK）。"""

import logging
import os
import time

from .base import LLMClient

logger = logging.getLogger(__name__)
DEFAULT_VERTEX_MODEL = "gemini-2.5-flash-lite"


class VertexClient(LLMClient):
    """google-genai SDK を使用した Vertex AI Gemini クライアント。"""

    def __init__(self) -> None:
        self.project_id = os.environ.get("VERTEX_PROJECT_ID", "")
        self.location = os.environ.get("VERTEX_LOCATION", "asia-northeast1")
        self.model_name = os.environ.get(
            "VERTEX_MODEL", DEFAULT_VERTEX_MODEL
        )
        self._client = None

    def _get_client(self):
        """genai.Client の遅延初期化。"""
        if self._client is None:
            from google import genai

            self._client = genai.Client(
                vertexai=True,
                project=self.project_id,
                location=self.location,
            )
        return self._client

    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Vertex AI Gemini でテキスト生成を実行する。"""
        start = time.monotonic()
        try:
            from google.genai import types

            client = self._get_client()
            response = await client.aio.models.generate_content(
                model=self.model_name,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    max_output_tokens=1024,
                    temperature=0.3,
                ),
            )
            duration_ms = int((time.monotonic() - start) * 1000)
            logger.info(
                "Vertex AI 生成完了",
                extra={"status": "completed", "duration_ms": duration_ms},
            )
            return response.text.strip()
        except Exception:
            duration_ms = int((time.monotonic() - start) * 1000)
            logger.exception(
                "Vertex AI による生成に失敗しました",
                extra={"status": "failed", "duration_ms": duration_ms},
            )
            return ""

    async def check_available(self) -> bool:
        """VERTEX_PROJECT_ID が設定されていれば利用可能とみなす。"""
        return bool(self.project_id)
