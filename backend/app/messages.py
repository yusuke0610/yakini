import json
from pathlib import Path
from typing import Any

_messages: dict[str, Any] = {}


def load_messages() -> None:
    """起動時にメッセージ定義を読み込む。"""
    global _messages
    path = Path(__file__).parent / "messages.json"
    with path.open(encoding="utf-8") as file:
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
    """正常系メッセージを取得する。

    現在はバックエンドのレスポンスに成功メッセージを含めていないため
    未使用だが、将来 API レスポンスに成功メッセージを含める際に使用する。
    """
    return _get_message("success", key, **kwargs)
