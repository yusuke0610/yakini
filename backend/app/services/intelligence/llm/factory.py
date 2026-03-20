"""LLM クライアントのファクトリ。"""

import logging
import os

from .base import LLMClient

logger = logging.getLogger(__name__)


def get_llm_client() -> LLMClient:
    """環境変数 LLM_PROVIDER に応じた LLM クライアントを返す。

    - ``"ollama"`` (デフォルト): OllamaClient
    - ``"vertex"``: VertexClient (google-cloud-aiplatform が必要)
    """
    provider = os.environ.get("LLM_PROVIDER", "ollama").lower()

    if provider == "vertex":
        from .vertex_client import VertexClient

        logger.info("LLM バックエンド: Vertex AI")
        return VertexClient()

    from .ollama_client import OllamaClient

    logger.info("LLM バックエンド: Ollama")
    return OllamaClient()
