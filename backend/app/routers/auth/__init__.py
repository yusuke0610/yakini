"""
auth ルーターパッケージ。

外部から `router` をインポートできるようにエクスポートする。
"""

from .endpoints import router

__all__ = ["router"]
