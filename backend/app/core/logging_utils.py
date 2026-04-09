"""構造化ログユーティリティ。

Cloud Run 上では標準出力に JSON を書くだけで Cloud Logging が収集する。
severity フィールドにより Cloud Logging のログレベルとして自動認識される。

**機密情報保護**: ログに氏名・住所・電話番号・メールアドレス・
トークン・Cookie・暗号化前の平文データを絶対に含めないこと。
許可されるフィールド: user_id, task_id, record_id, status, duration_ms,
error_type, http_status 等の識別子・メトリクスのみ。
"""

import json
import logging
import os
import sys
from typing import Any

logger = logging.getLogger("devforge")

_SEVERITY_MAP = {
    logging.DEBUG: "DEBUG",
    logging.INFO: "INFO",
    logging.WARNING: "WARNING",
    logging.ERROR: "ERROR",
    logging.CRITICAL: "CRITICAL",
}

# 構造化フィールドとして JSON ペイロードに含めるキー
_STRUCTURED_KEYS = frozenset(
    {
        "task_id",
        "user_id",
        "record_id",
        "status",
        "duration_ms",
        "error_type",
        "http_status",
        "error_id",
    }
)


class CloudLoggingFormatter(logging.Formatter):
    """Cloud Logging が severity として認識する JSON フォーマッター。"""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "severity": _SEVERITY_MAP.get(record.levelno, "DEFAULT"),
            "message": record.getMessage(),
            "logger": record.name,
        }
        for key in _STRUCTURED_KEYS:
            value = getattr(record, key, None)
            if value is not None:
                payload[key] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def setup_logging() -> None:
    """ルートロガーを構成する。Cloud 環境では JSON、ローカルでは通常形式。"""
    root = logging.getLogger()
    # 多重追加を防止
    if root.handlers:
        return

    handler = logging.StreamHandler(sys.stdout)
    env = os.getenv("ENVIRONMENT", "local")
    if env in ("dev", "stg", "prod"):
        handler.setFormatter(CloudLoggingFormatter())

    root.setLevel(logging.INFO)
    root.addHandler(handler)


def log_event(level: int, event: str, **fields: Any) -> None:
    """構造化フィールド付きのイベントログを出力する。"""
    logger.log(level, event, extra={k: v for k, v in fields.items() if k in _STRUCTURED_KEYS})
