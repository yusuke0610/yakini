"""バックグラウンドタスクのワーカー。

ローカル: BackgroundTasks から直接呼ばれる（retry_count=0, max_attempts=1 でリトライなし）。
Cloud: /internal/tasks/{type} エンドポイント経由で呼ばれる（Cloud Tasks ネイティブリトライ）。
どちらも同じ ``execute_task`` を経由してハンドラレジストリにディスパッチする。

タスク種別ごとの実体は ``services/tasks/handlers/`` 配下に分離されている。worker は
リトライ・dead_letter・通知などのタスク横断ロジックのみを担う。
"""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from ...core.logging_utils import get_logger
from ...core.messages import get_notification
from ...db.database import SessionLocal
from ...repositories.notification import NotificationRepository
from .base import TaskType
from .exceptions import NonRetryableError
from .handlers import get_handler

logger = get_logger(__name__)


# duration_ms がこの閾値を超えたら WARNING を出す（5分）
_SLOW_TASK_THRESHOLD_MS = 300_000


def _monotonic_ms_since(start: float) -> int:
    """``time.monotonic()`` の開始時点からの経過ミリ秒を返す。"""
    import time
    return int((time.monotonic() - start) * 1000)


async def execute_task(
    task_type: TaskType,
    payload: dict,
    *,
    retry_count: int = 0,
    max_attempts: int = 1,
) -> None:
    """タスクを実行する。自前で DB セッションを作成・管理する。

    retry_count: Cloud Tasks の ``X-CloudTasks-TaskRetryCount`` ヘッダー値（0 始まり）。
    max_attempts: Cloud Tasks キューの ``retry_config.max_attempts``（総試行回数）。

    ローカル（BackgroundTasks）呼び出しではデフォルトの ``retry_count=0, max_attempts=1`` を使い、
    失敗時は即座に ``dead_letter`` へ遷移する（ローカルはネイティブリトライが無いため）。
    """
    import time

    user_id = payload.get("user_id", "unknown")
    record_id = payload.get("record_id")
    start = time.monotonic()

    logger.info(
        "タスク開始",
        extra={
            "task_id": task_type.value,
            "user_id": user_id,
            "record_id": record_id,
            "status": "running",
            "retry_count": retry_count,
            "max_attempts": max_attempts,
        },
    )

    if get_handler(task_type) is None:
        logger.error("不明なタスク種別: %s", task_type)
        return

    db = SessionLocal()
    try:
        # 各 ``_run_*`` シムはテストからの patch ポイントとして残している。
        # 実体は ``services/tasks/handlers/`` 配下のハンドラ。
        if task_type == TaskType.GITHUB_ANALYSIS:
            await _run_github_analysis(db, payload)
        elif task_type == TaskType.BLOG_SUMMARIZE:
            await _run_blog_summarize(db, payload)
        elif task_type == TaskType.CAREER_ANALYSIS:
            await _run_career_analysis(db, payload)

        duration_ms = _monotonic_ms_since(start)
        logger.info(
            "タスク完了",
            extra={
                "task_id": task_type.value,
                "user_id": user_id,
                "record_id": record_id,
                "status": "completed",
                "duration_ms": duration_ms,
                "retry_count": retry_count,
            },
        )
        if duration_ms > _SLOW_TASK_THRESHOLD_MS:
            logger.warning(
                "タスクが低速です (%d ms)",
                duration_ms,
                extra={"task_id": task_type.value, "user_id": user_id, "duration_ms": duration_ms},
            )
        if isinstance(user_id, str) and user_id != "unknown":
            _create_notification(db, task_type, user_id, "completed")
    except NonRetryableError as exc:
        duration_ms = _monotonic_ms_since(start)
        logger.warning(
            "タスク失敗（リトライ不可）",
            extra={
                "task_id": task_type.value,
                "user_id": user_id,
                "record_id": record_id,
                "status": "dead_letter",
                "error_type": type(exc).__name__,
                "duration_ms": duration_ms,
                "retry_count": retry_count,
            },
            exc_info=True,
        )
        _safe_rollback(db)
        _mark_dead_letter(db, task_type, payload, error=exc)
        if isinstance(user_id, str) and user_id != "unknown":
            _create_notification(db, task_type, user_id, "failed")
        raise
    except Exception as exc:
        duration_ms = _monotonic_ms_since(start)
        is_final = retry_count >= max_attempts - 1
        if is_final:
            logger.error(
                "タスクが最終試行で失敗しました (dead_letter)",
                extra={
                    "task_id": task_type.value,
                    "user_id": user_id,
                    "record_id": record_id,
                    "status": "dead_letter",
                    "error_type": type(exc).__name__,
                    "duration_ms": duration_ms,
                    "retry_count": retry_count,
                    "max_attempts": max_attempts,
                },
                exc_info=True,
            )
            _safe_rollback(db)
            _mark_dead_letter(db, task_type, payload, error=exc)
            if isinstance(user_id, str) and user_id != "unknown":
                _create_notification(db, task_type, user_id, "failed")
        else:
            logger.warning(
                "タスク失敗（リトライ予定）",
                extra={
                    "task_id": task_type.value,
                    "user_id": user_id,
                    "record_id": record_id,
                    "status": "retrying",
                    "error_type": type(exc).__name__,
                    "duration_ms": duration_ms,
                    "retry_count": retry_count,
                    "max_attempts": max_attempts,
                },
                exc_info=True,
            )
            _safe_rollback(db)
            _mark_retrying(db, task_type, payload, retry_count, max_attempts, error=exc)
        raise
    finally:
        db.close()


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ---------- ハンドラ薄ラッパー（後方互換）----------
# テストや既存呼び出しから ``_run_github_analysis`` / ``_run_blog_summarize`` /
# ``_run_career_analysis`` を直接呼べるよう、ハンドラ実装への薄いシムを残す。


async def _run_github_analysis(db: Session, payload: dict) -> None:
    """GitHub 分析ハンドラへのシム。"""
    handler = get_handler(TaskType.GITHUB_ANALYSIS)
    assert handler is not None
    await handler.run(db, payload)


async def _run_blog_summarize(db: Session, payload: dict) -> None:
    """ブログサマリハンドラへのシム。"""
    handler = get_handler(TaskType.BLOG_SUMMARIZE)
    assert handler is not None
    await handler.run(db, payload)


async def _run_career_analysis(db: Session, payload: dict) -> None:
    """キャリア分析ハンドラへのシム。"""
    handler = get_handler(TaskType.CAREER_ANALYSIS)
    assert handler is not None
    await handler.run(db, payload)


# ---------- 共通 ----------


def _safe_rollback(db: Session) -> None:
    """タスク失敗時にセッションをロールバックする。

    DB コミット失敗後はセッションが PendingRollbackError 状態になり、
    後続の _mark_dead_letter/_mark_retrying が commit できなくなる。
    ロールバックで状態をリセットしてから status 更新を実行するために呼ぶ。
    """
    try:
        db.rollback()
    except Exception:
        logger.warning("セッションのロールバックに失敗しました", exc_info=True)


def _create_notification(db: Session, task_type: TaskType, user_id: str, status: str) -> None:
    """タスク完了・失敗時に通知を作成する。失敗しても例外を握りつぶす（通知は補助機能）。"""
    try:
        title = get_notification(task_type.value, status)
        NotificationRepository.create(
            db=db, user_id=user_id, task_type=task_type.value, status=status, title=title
        )
    except Exception:
        logger.warning("通知の作成に失敗しました（タスク処理には影響しません）", exc_info=True)


def _get_task_record(db: Session, task_type: TaskType, payload: dict):
    """タスク種別に応じた DB レコードを取得する（ハンドラに委譲）。"""
    handler = get_handler(task_type)
    if handler is None:
        return None
    return handler.get_record(db, payload)


def _mark_dead_letter(
    db: Session,
    task_type: TaskType,
    payload: dict,
    *,
    error: Exception | None = None,
) -> None:
    """タスクを終端ステータス（``dead_letter``）に更新する。

    リトライ不可（NonRetryableError）またはリトライ上限に達したエラーで呼ばれる。
    失敗ステータスは ``dead_letter`` に一本化している。
    """
    try:
        error_message = str(error) if error else "予期しないエラーが発生しました"
        record = _get_task_record(db, task_type, payload)
        if record and record.status != "completed":
            record.status = "dead_letter"
            record.error_message = error_message
            record.completed_at = _now()
            db.commit()
    except Exception:
        logger.exception("タスク失敗マーク中にエラーが発生しました")


def _mark_retrying(
    db: Session,
    task_type: TaskType,
    payload: dict,
    retry_count: int,
    max_attempts: int,
    *,
    error: Exception | None = None,
) -> None:
    """タスクをリトライ待ち状態（``retrying``）に更新する。"""
    try:
        record = _get_task_record(db, task_type, payload)
        if record and record.status != "completed":
            record.status = "retrying"
            record.retry_count = retry_count
            record.max_retries = max_attempts
            if error is not None:
                record.error_message = str(error)
            db.commit()
    except Exception:
        logger.exception("タスクリトライマーク中にエラーが発生しました")
