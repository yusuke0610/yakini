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

        client = VertexClient()
        logger.info(
            "LLM backend: vertex (model=%s, project=%s, location=%s)",
            client.model_name, client.project_id, client.location,
        )
        return client

    from .ollama_client import OllamaClient

    client = OllamaClient()
    logger.info("LLM backend: ollama (model=%s)", client.model)
    return client
