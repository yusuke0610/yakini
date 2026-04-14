"""Redis クライアント（Upstash Redis）。"""

import logging
import os

logger = logging.getLogger(__name__)

# モジュールレベルのシングルトン（初回呼び出し時に初期化）
_client = None
_initialized = False


def get_redis_client():
    """Upstash Redis 非同期クライアントを返す。

    未設定または接続失敗時は None を返す。
    タスクが Redis 障害で止まらないよう、呼び出し元で None チェックすること。
    """
    global _client, _initialized
    if _initialized:
        return _client

    _initialized = True
    url = os.getenv("UPSTASH_REDIS_URL", "").strip()
    token = os.getenv("UPSTASH_REDIS_TOKEN", "").strip()

    if not url:
        return None

    try:
        import redis.asyncio as aioredis

        _client = aioredis.from_url(
            url,
            password=token if token else None,
            decode_responses=True,
            ssl_cert_reqs=None,
        )
        return _client
    except Exception:
        logger.warning("Redis クライアントの初期化に失敗しました", exc_info=True)
        return None
