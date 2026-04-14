import json
from pathlib import Path
from typing import Any

_messages: dict[str, Any] = {}
_MESSAGES_PATH = Path(__file__).resolve().parents[1] / "messages.json"


def load_messages() -> None:
    """起動時にメッセージ定義を読み込む。"""
    global _messages
    with _MESSAGES_PATH.open(encoding="utf-8") as file:
        _messages = json.load(file)


def _get_message(category: str, key: str, **kwargs: str) -> str:
    if not _messages:
        load_messages()

    message: Any = _messages.get(category, {})
    for part in key.split("."):
        if not isinstance(message, dict):
            return key
        message = message.get(part)
        if message is None:
            return key

    if not isinstance(message, str):
        return key
    if kwargs:
        return message.format(**kwargs)
    return message


def get_error(key: str, **kwargs: str) -> str:
    """エラーメッセージを取得する。"""
    return _get_message("error", key, **kwargs)


def get_success(key: str, **kwargs: str) -> str:
    """正常系メッセージを取得する。"""
    return _get_message("success", key, **kwargs)


def get_notification(task_type: str, status: str) -> str:
    """通知タイトルを取得する。status は 'completed' or 'failed'。"""
    return _get_message("notification", f"{task_type}.{status}")
