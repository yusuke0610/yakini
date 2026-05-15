"""ブログ AI サマリタスクのハンドラ。"""

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from ....core.logging_utils import get_logger
from ....models import BlogSummaryCache
from ....repositories import BlogArticleRepository
from .base import TaskHandler

logger = get_logger(__name__)


# サマリ結果の保持期間（DB 取得時にこの期間を過ぎていれば破棄して再生成を促す）
_SUMMARY_TTL = timedelta(days=7)


def _now() -> datetime:
    return datetime.now(timezone.utc)


class BlogSummarizeHandler(TaskHandler):
    """ブログ記事の AI サマリ生成タスク。"""

    def get_record(self, db: Session, payload: dict) -> BlogSummaryCache | None:
        user_id = payload.get("user_id")
        if not user_id:
            return None
        return db.query(BlogSummaryCache).filter_by(user_id=user_id).first()

    async def run(self, db: Session, payload: dict) -> None:
        from ...intelligence.llm import get_llm_client
        from ...intelligence.llm_summarizer import summarize_blog_articles

        user_id = payload.get("user_id")
        if not user_id:
            logger.error("ペイロードに user_id がありません", extra={"payload_keys": list(payload.keys())})
            return
        cache = self.get_record(db, payload)
        if not cache:
            logger.error("ブログサマリキャッシュが見つかりません", extra={"user_id": user_id})
            return

        cache.status = "processing"
        cache.started_at = _now()
        db.commit()

        # 記事は payload ではなく DB から取得する（GET /api/blog/articles と同じソース）
        article_rows = BlogArticleRepository(db, user_id).list_by_user()
        if not article_rows:
            cache.status = "dead_letter"
            cache.error_message = "分析対象の記事がありません"
            cache.completed_at = _now()
            db.commit()
            return

        articles_data = [
            {
                "title": art.title,
                "url": art.url,
                "published_at": art.published_at,
                "likes_count": art.likes_count,
                "summary": art.summary,
                "tags": art.tags,
                "platform": art.platform,
            }
            for art in article_rows
        ]

        llm_client = get_llm_client()
        if not await llm_client.check_available():
            cache.status = "dead_letter"
            cache.error_message = "LLM サービスが利用できません"
            cache.completed_at = _now()
            db.commit()
            return

        summary = await summarize_blog_articles(articles_data)
        if not summary:
            cache.status = "dead_letter"
            cache.error_message = "LLM処理が利用できません"
            cache.completed_at = _now()
            db.commit()
            return

        cache.summary = summary
        cache.status = "completed"
        cache.error_message = None
        cache.completed_at = _now()
        cache.expires_at = _now() + _SUMMARY_TTL
        db.commit()
