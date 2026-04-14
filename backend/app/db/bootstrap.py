import logging
from datetime import datetime, timezone

from ..core.logging_utils import log_event
from .migrations import run_migrations
from .sqlite_backup import restore_sqlite_from_gcs_if_configured


def bootstrap() -> None:
    restored = restore_sqlite_from_gcs_if_configured()
    log_event(
        logging.INFO,
        "sqlite_bootstrap_restore_result",
        restored=restored,
    )
    run_migrations()
    log_event(logging.INFO, "sqlite_bootstrap_migration_succeeded")

    from .database import SessionLocal
    from .seed import seed_master_data

    db = SessionLocal()
    try:
        seed_master_data(db)
        log_event(logging.INFO, "sqlite_bootstrap_seed_succeeded")
        _reset_orphaned_tasks(db)
    finally:
        db.close()


def _reset_orphaned_tasks(db) -> None:
    """サーバ再起動で宙吊りになった pending/processing タスクを failed にリセットする。

    BackgroundTasks はプロセス内コルーチンのため、サーバが強制終了されると
    _mark_failed() が呼ばれずに DB ステータスが pending/processing のまま残る。
    放置すると次回起動時にフロントエンドが無限ポーリングに陥るため、起動時に掃除する。
    """
    from ..models.cache import BlogSummaryCache, GitHubAnalysisCache
    from ..models.career_analysis import CareerAnalysis

    logger = logging.getLogger(__name__)
    now = datetime.now(timezone.utc)
    stale_statuses = ("pending", "processing")
    error_message = "サーバ再起動により処理が中断されました"

    # CareerAnalysis
    ca_rows = (
        db.query(CareerAnalysis)
        .filter(CareerAnalysis.status.in_(stale_statuses))
        .all()
    )
    for row in ca_rows:
        row.status = "failed"
        row.error_message = error_message
        row.completed_at = now
    if ca_rows:
        logger.warning(
            "孤立したキャリア分析タスクをリセットしました",
            extra={"count": len(ca_rows)},
        )

    # GitHubAnalysisCache
    gh_rows = (
        db.query(GitHubAnalysisCache)
        .filter(GitHubAnalysisCache.status.in_(stale_statuses))
        .all()
    )
    for row in gh_rows:
        row.status = "failed"
        row.error_message = error_message
        row.completed_at = now
    if gh_rows:
        logger.warning(
            "孤立した GitHub 分析タスクをリセットしました",
            extra={"count": len(gh_rows)},
        )

    # BlogSummaryCache
    blog_rows = (
        db.query(BlogSummaryCache)
        .filter(BlogSummaryCache.status.in_(stale_statuses))
        .all()
    )
    for row in blog_rows:
        row.status = "failed"
        row.error_message = error_message
        row.completed_at = now
    if blog_rows:
        logger.warning(
            "孤立したブログ AI 分析タスクをリセットしました",
            extra={"count": len(blog_rows)},
        )

    db.commit()


if __name__ == "__main__":
    bootstrap()
