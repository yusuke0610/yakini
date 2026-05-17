"""tests/test_worker パッケージ内で共有するヘルパ。"""

import asyncio


def run_sync(coro):
    """async 関数を同期的に実行するヘルパー。"""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()
