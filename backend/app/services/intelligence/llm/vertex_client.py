"""Vertex AI Gemini バックエンドクライアント。"""

import logging
import os

from .base import LLMClient

logger = logging.getLogger(__name__)


class VertexClient(LLMClient):
    """Vertex AI Gemini を使用した LLM クライアント。"""

    def __init__(self) -> None:
        self.project_id = os.environ.get("VERTEX_PROJECT_ID", "")
        self.location = os.environ.get("VERTEX_LOCATION", "asia-northeast1")
        self.model_name = os.environ.get("VERTEX_MODEL", "gemini-2.0-flash")
        self._initialized = False

    def _ensure_init(self):
        """Vertex AI SDK の初期化を遅延実行する。"""
        if self._initialized:
            return
        import vertexai
        vertexai.init(project=self.project_id, location=self.location)
        self._initialized = True

    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Vertex AI Gemini でテキスト生成を実行する。"""
        try:
            self._ensure_init()
            from vertexai.generative_models import GenerativeModel

            model = GenerativeModel(
                self.model_name,
                system_instruction=system_prompt,
            )
            response = await model.generate_content_async(user_prompt)
            return response.text.strip()
        except Exception:
            logger.exception("Vertex AI による要約生成に失敗しました")
            return ""

    async def check_available(self) -> bool:
        """VERTEX_PROJECT_ID が設定されていれば利用可能とみなす。"""
        return bool(self.project_id)
