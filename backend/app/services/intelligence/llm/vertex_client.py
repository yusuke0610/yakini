"""Vertex AI Gemini バックエンドクライアント（google-genai SDK）。"""

import asyncio
import logging
import os
import time

from ....services.tasks.exceptions import NonRetryableError, RetryableError
from .base import LLMClient

logger = logging.getLogger(__name__)
DEFAULT_VERTEX_MODEL = "gemini-2.5-flash-lite"

# 一時障害とみなす HTTP ステータスコード
_RETRYABLE_STATUS_CODES = {408, 425, 429, 500, 502, 503, 504}


def _extract_usage(response) -> dict[str, int]:
    """Vertex レスポンスの ``usage_metadata`` からトークン数を抜き出す。

    SDK バージョンや部分障害でフィールドが欠ける可能性があるので、
    取れたものだけを dict で返す。計測用途なので失敗しても握りつぶす。
    """
    meta = getattr(response, "usage_metadata", None)
    if meta is None:
        return {}
    fields = {
        "prompt_tokens": "prompt_token_count",
        "output_tokens": "candidates_token_count",
        "total_tokens": "total_token_count",
        "cached_tokens": "cached_content_token_count",
    }
    out: dict[str, int] = {}
    for key, attr in fields.items():
        value = getattr(meta, attr, None)
        if isinstance(value, int):
            out[key] = value
    return out


def _parse_retry_after(exc: Exception) -> float | None:
    """APIError.response から ``Retry-After`` ヘッダを抽出する。"""
    response = getattr(exc, "response", None)
    if response is None:
        return None
    headers = getattr(response, "headers", None) or {}
    value = headers.get("retry-after") or headers.get("Retry-After")
    if not value:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


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

    async def generate(self, system_prompt: str, user_prompt: str) -> str | None:
        """Vertex AI Gemini でテキスト生成を実行する。

        一時障害は ``RetryableError``、恒久的な障害は ``NonRetryableError`` を
        raise する。未分類の例外は ``None`` を返す。
        """
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
                extra={
                    "status": "completed",
                    "duration_ms": duration_ms,
                    **_extract_usage(response),
                },
            )
            return response.text.strip()
        except (asyncio.TimeoutError, TimeoutError) as exc:
            duration_ms = int((time.monotonic() - start) * 1000)
            logger.warning(
                "Vertex AI 生成がタイムアウトしました",
                extra={"status": "failed", "duration_ms": duration_ms},
            )
            raise RetryableError(f"Vertex AI タイムアウト: {exc}") from exc
        except Exception as exc:
            duration_ms = int((time.monotonic() - start) * 1000)
            classified = _classify_vertex_exception(exc)
            if classified is not None:
                logger.warning(
                    "Vertex AI による生成に失敗しました (%s)",
                    type(classified).__name__,
                    extra={"status": "failed", "duration_ms": duration_ms},
                )
                raise classified from exc
            logger.exception(
                "Vertex AI による生成に失敗しました",
                extra={"status": "failed", "duration_ms": duration_ms},
            )
            return None

    async def check_available(self) -> bool:
        """VERTEX_PROJECT_ID が設定されていれば利用可能とみなす。"""
        return bool(self.project_id)


def _classify_vertex_exception(exc: Exception) -> Exception | None:
    """Vertex AI / google-genai の例外をリトライ可否で分類する。

    分類できた場合は ``RetryableError`` / ``NonRetryableError`` を返し、
    呼び出し元は ``raise`` する。分類できなければ ``None`` を返す。
    """
    # google-genai SDK の APIError ファミリー（code 属性で HTTP ステータスを持つ）
    try:
        from google.genai.errors import APIError
    except ImportError:
        APIError = None  # type: ignore[assignment]

    if APIError is not None and isinstance(exc, APIError):
        code = getattr(exc, "code", None)
        if isinstance(code, int):
            if code in _RETRYABLE_STATUS_CODES:
                retry_after = _parse_retry_after(exc) if code == 429 else None
                return RetryableError(
                    f"Vertex AI {code}: {exc}", retry_after=retry_after
                )
            if 400 <= code < 500:
                return NonRetryableError(f"Vertex AI {code}: {exc}")

    # google.api_core 例外のフォールバック（低レベル呼び出しから伝播するケース）
    try:
        from google.api_core import exceptions as gax
    except ImportError:
        return None

    if isinstance(
        exc,
        (
            gax.DeadlineExceeded,
            gax.ResourceExhausted,
            gax.ServiceUnavailable,
            gax.InternalServerError,
            gax.TooManyRequests,
        ),
    ):
        retry_after = _parse_retry_after(exc) if isinstance(exc, gax.TooManyRequests) else None
        return RetryableError(
            f"Vertex AI {type(exc).__name__}: {exc}", retry_after=retry_after
        )
    if isinstance(
        exc,
        (
            gax.InvalidArgument,
            gax.PermissionDenied,
            gax.NotFound,
            gax.Unauthenticated,
            gax.BadRequest,
        ),
    ):
        return NonRetryableError(f"Vertex AI {type(exc).__name__}: {exc}")
    return None
