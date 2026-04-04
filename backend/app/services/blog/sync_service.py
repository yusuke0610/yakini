"""ブログアカウント同期サービス。

外部 API からの記事取得・正規化・DB保存のロジックを router から分離する。
"""

import logging

from sqlalchemy.orm import Session

from ...repositories import BlogAccountRepository, BlogArticleRepository
from ...schemas import BlogSyncResponse
from .collector import (
    BlogPlatformRequestError,
    UnsupportedBlogPlatformError,
    fetch_articles,
)

logger = logging.getLogger(__name__)


class BlogSyncService:
    """ブログアカウントの同期処理を担うサービスクラス。"""

    def __init__(self, db: Session, user_id: str) -> None:
        self._db = db
        self._user_id = user_id
        self._account_repo = BlogAccountRepository(db, user_id)
        self._article_repo = BlogArticleRepository(db, user_id)

    def get_account_or_none(self, account_id: str):
        """指定 ID のアカウントを返す。存在しない場合は None。"""
        return self._account_repo.get_by_id(account_id)

    async def sync(self, account_id: str) -> BlogSyncResponse:
        """外部 API からデータを取得して DB に保存し、同期結果を返す。

        Raises:
            UnsupportedBlogPlatformError: サポート外のプラットフォームの場合。
            BlogPlatformRequestError: 外部 API リクエストに失敗した場合。
        """
        account = self._account_repo.get_by_id(account_id)
        if not account:
            raise ValueError(f"アカウントが見つかりません: {account_id}")

        try:
            raw_articles = await fetch_articles(account.platform, account.username)
        except UnsupportedBlogPlatformError:
            raise
        except Exception:
            logger.exception(
                "ブログ記事の取得に失敗しました: %s/%s",
                account.platform,
                account.username,
            )
            raise BlogPlatformRequestError(
                f"記事取得に失敗しました: {account.platform}/{account.username}"
            )

        for art in raw_articles:
            art["account_id"] = account.id

        synced = self._article_repo.upsert_many(raw_articles)
        total = self._article_repo.count_by_user()

        return BlogSyncResponse(synced_count=synced, total_count=total)
