"""LLM クライアント抽象化レイヤーのテスト。"""

import asyncio
import os
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
from app.services.intelligence.llm.factory import get_llm_client
from app.services.intelligence.llm.ollama_client import OllamaClient
from app.services.intelligence.llm.vertex_client import DEFAULT_VERTEX_MODEL, VertexClient


def _run(coro):
    """async 関数を同期的に実行するヘルパー。"""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# ---------- OllamaClient ----------


def test_ollama_generate_success():
    """Ollama の正常系: レスポンスからテキストを取得する。"""
    client = OllamaClient()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {"response": " テスト要約 "}

    with patch("httpx.AsyncClient") as mock_cls:
        mock_http = AsyncMock()
        mock_http.post.return_value = mock_response
        mock_http.__aenter__ = AsyncMock(return_value=mock_http)
        mock_http.__aexit__ = AsyncMock(return_value=False)
        mock_cls.return_value = mock_http

        result = _run(client.generate("system", "user"))
        assert result == "テスト要約"
        mock_http.post.assert_called_once()


def test_ollama_generate_connect_error():
    """Ollama 接続エラー時に空文字列を返す。"""
    client = OllamaClient()

    with patch("httpx.AsyncClient") as mock_cls:
        mock_http = AsyncMock()
        mock_http.post.side_effect = httpx.ConnectError("接続失敗")
        mock_http.__aenter__ = AsyncMock(return_value=mock_http)
        mock_http.__aexit__ = AsyncMock(return_value=False)
        mock_cls.return_value = mock_http

        result = _run(client.generate("system", "user"))
        assert result == ""


def test_ollama_check_available_success():
    """Ollama ヘルスチェック: 200 で True を返す。"""
    client = OllamaClient()
    mock_response = MagicMock()
    mock_response.status_code = 200

    with patch("httpx.AsyncClient") as mock_cls:
        mock_http = AsyncMock()
        mock_http.get.return_value = mock_response
        mock_http.__aenter__ = AsyncMock(return_value=mock_http)
        mock_http.__aexit__ = AsyncMock(return_value=False)
        mock_cls.return_value = mock_http

        assert _run(client.check_available()) is True


def test_ollama_check_available_timeout():
    """Ollama ヘルスチェック: タイムアウトで False を返す。"""
    client = OllamaClient()

    with patch("httpx.AsyncClient") as mock_cls:
        mock_http = AsyncMock()
        mock_http.get.side_effect = httpx.TimeoutException("タイムアウト")
        mock_http.__aenter__ = AsyncMock(return_value=mock_http)
        mock_http.__aexit__ = AsyncMock(return_value=False)
        mock_cls.return_value = mock_http

        assert _run(client.check_available()) is False


def test_ollama_uses_lightweight_defaults():
    """既定では軽量モデルと長めのタイムアウトを使う。"""
    env = os.environ.copy()
    env.pop("OLLAMA_MODEL", None)
    env.pop("OLLAMA_TIMEOUT", None)

    with patch.dict(os.environ, env, clear=True):
        client = OllamaClient()

    assert client.model == "gemma4:31b"
    assert client.timeout == 1200.0


# ---------- VertexClient ----------


def test_vertex_generate_success():
    """Vertex AI の正常系: google-genai Client をモックしてテキスト取得。"""
    with patch.dict(os.environ, {"VERTEX_PROJECT_ID": "test-project"}):
        client = VertexClient()

    mock_response = MagicMock()
    mock_response.text = " テスト要約 "

    mock_generate = AsyncMock(return_value=mock_response)
    mock_models = MagicMock()
    mock_models.generate_content = mock_generate
    mock_aio = MagicMock()
    mock_aio.models = mock_models
    mock_genai_client = MagicMock()
    mock_genai_client.aio = mock_aio

    client._client = mock_genai_client
    result = _run(client.generate("system", "user"))
    assert result == "テスト要約"
    mock_generate.assert_called_once()


def test_vertex_generate_exception():
    """Vertex AI で例外発生時に空文字列を返す。"""
    with patch.dict(os.environ, {"VERTEX_PROJECT_ID": "test-project"}):
        client = VertexClient()

    mock_generate = AsyncMock(side_effect=Exception("API エラー"))
    mock_models = MagicMock()
    mock_models.generate_content = mock_generate
    mock_aio = MagicMock()
    mock_aio.models = mock_models
    mock_genai_client = MagicMock()
    mock_genai_client.aio = mock_aio

    client._client = mock_genai_client
    result = _run(client.generate("system", "user"))
    assert result == ""


def test_vertex_check_available_with_project():
    """VERTEX_PROJECT_ID があれば True。"""
    with patch.dict(os.environ, {"VERTEX_PROJECT_ID": "test-project"}):
        client = VertexClient()
    assert _run(client.check_available()) is True


def test_vertex_check_available_without_project():
    """VERTEX_PROJECT_ID がなければ False。"""
    env = os.environ.copy()
    env.pop("VERTEX_PROJECT_ID", None)
    with patch.dict(os.environ, env, clear=True):
        client = VertexClient()
    assert _run(client.check_available()) is False


def test_vertex_uses_supported_default_model():
    """VERTEX_MODEL 未設定時はサポート中の既定モデルを使う。"""
    env = os.environ.copy()
    env.pop("VERTEX_MODEL", None)
    with patch.dict(os.environ, env, clear=True):
        client = VertexClient()
    assert client.model_name == DEFAULT_VERTEX_MODEL


# ---------- ファクトリ ----------


def test_factory_returns_ollama_by_default():
    """デフォルトで OllamaClient を返す。"""
    env = os.environ.copy()
    env.pop("LLM_PROVIDER", None)
    with patch.dict(os.environ, env, clear=True):
        client = get_llm_client()
    assert isinstance(client, OllamaClient)


def test_factory_returns_ollama_explicitly():
    """LLM_PROVIDER=ollama で OllamaClient を返す。"""
    with patch.dict(os.environ, {"LLM_PROVIDER": "ollama"}):
        client = get_llm_client()
    assert isinstance(client, OllamaClient)


def test_factory_returns_vertex():
    """LLM_PROVIDER=vertex で VertexClient を返す。"""
    with patch.dict(os.environ, {"LLM_PROVIDER": "vertex"}):
        client = get_llm_client()
    assert isinstance(client, VertexClient)
