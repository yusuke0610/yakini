"""LLM クライアントの基底クラス。"""

from abc import ABC, abstractmethod


class LLMClient(ABC):
    """LLM バックエンド共通インターフェース。"""

    @abstractmethod
    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        """テキスト生成を実行する。失敗時は空文字列を返す。"""

    @abstractmethod
    async def check_available(self) -> bool:
        """バックエンドが利用可能か確認する。"""
