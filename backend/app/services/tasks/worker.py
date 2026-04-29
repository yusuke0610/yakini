"""バックグラウンドタスクのワーカー。

ローカル: BackgroundTasks から直接呼ばれる（retry_count=0, max_attempts=1 でリトライなし）。
Cloud: /internal/tasks/{type} エンドポイント経由で呼ばれる（Cloud Tasks ネイティブリトライ）。
どちらも同じ関数を実行する。
"""

import json
import time
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from ...core.logging_utils import get_logger
from ...core.messages import get_notification
from ...db.database import SessionLocal
from ...models import BlogSummaryCache, GitHubAnalysisCache
from ...models.career_analysis import CareerAnalysis
from ...repositories.notification import NotificationRepository
from ...services.intelligence.llm import get_llm_client
from .base import TaskType
from .exceptions import NonRetryableError

logger = get_logger(__name__)


# duration_ms がこの閾値を超えたら WARNING を出す（5分）
_SLOW_TASK_THRESHOLD_MS = 300_000



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

    db = SessionLocal()
    try:
        if task_type == TaskType.GITHUB_ANALYSIS:
            await _run_github_analysis(db, payload)
        elif task_type == TaskType.BLOG_SUMMARIZE:
            await _run_blog_summarize(db, payload)
        elif task_type == TaskType.CAREER_ANALYSIS:
            await _run_career_analysis(db, payload)
        else:
            logger.error("不明なタスク種別: %s", task_type)
            return

        duration_ms = int((time.monotonic() - start) * 1000)
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
        duration_ms = int((time.monotonic() - start) * 1000)
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
        _mark_dead_letter(db, task_type, payload, error=exc)
        if isinstance(user_id, str) and user_id != "unknown":
            _create_notification(db, task_type, user_id, "failed")
        raise
    except Exception as exc:
        duration_ms = int((time.monotonic() - start) * 1000)
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
            _mark_retrying(db, task_type, payload, retry_count, max_attempts, error=exc)
        raise
    finally:
        db.close()


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ---------- GitHub 分析 ----------


async def _run_github_analysis(db: Session, payload: dict) -> None:
    """GitHub 分析パイプラインを実行し、AI 学習アドバイスまで一括生成してキャッシュに保存する。"""
    from collections import defaultdict
    from datetime import datetime

    from ...core.encryption import decrypt_field
    from ...services.intelligence.github_collector import (
        GitHubUserNotFoundError,
        collect_repos,
    )
    from ...services.intelligence.pipeline import IntelligenceResult
    from ...services.intelligence.position_scorer import calculate_position_scores
    from ...services.intelligence.response_mapper import map_pipeline_result
    from ...services.intelligence.skill_extractor import extract_skills
    from ...services.progress_service import set_progress

    _TOTAL_STEPS = 6
    user_id = payload["user_id"]
    task_id = user_id

    cache = db.query(GitHubAnalysisCache).filter_by(user_id=user_id).first()
    if not cache:
        logger.error("GitHub 分析キャッシュが見つかりません", extra={"user_id": user_id})
        return

    cache.status = "processing"
    cache.started_at = _now()
    db.commit()

    token = decrypt_field(payload["github_token"]) if payload.get("github_token") else None

    try:
        # ステップ 1: リポジトリ一覧取得
        await set_progress(task_id, 1, _TOTAL_STEPS, "リポジトリ一覧取得中...")

        async def _on_repo_fetched(done: int, total: int) -> None:
            await set_progress(
                task_id,
                2,
                _TOTAL_STEPS,
                "リポジトリ詳細取得中...",
                sub_progress={"done": done, "total": total},
            )

        repos = await collect_repos(
            username=payload["github_username"],
            token=token,
            include_forks=payload.get("include_forks", False),
            on_repo_fetched=_on_repo_fetched,
        )
    except GitHubUserNotFoundError as exc:
        cache.status = "dead_letter"
        cache.error_message = f"GitHubユーザーが見つかりません: {payload['github_username']}"
        cache.completed_at = _now()
        db.commit()
        raise exc

    # ステップ 3: スキル抽出
    await set_progress(task_id, 3, _TOTAL_STEPS, "スキル抽出中...")
    extraction = extract_skills(repos)

    lang_totals: dict = defaultdict(int)
    for repo in repos:
        for lang, byte_count in repo.languages.items():
            lang_totals[lang] += byte_count

    # 全リポジトリの検出フレームワークをユニーク化（最初の出現順を保持）
    all_frameworks: list[str] = []
    seen_frameworks: set[str] = set()
    for repo in repos:
        for fw in repo.detected_frameworks:
            if fw not in seen_frameworks:
                seen_frameworks.add(fw)
                all_frameworks.append(fw)

    # ステップ 4: スコア算出
    await set_progress(task_id, 4, _TOTAL_STEPS, "スコア算出中...")
    scores = calculate_position_scores(repos)

    result = IntelligenceResult(
        username=payload["github_username"],
        repos_analyzed=extraction.repos_analyzed,
        unique_skills=len(extraction.unique_skills),
        analyzed_at=datetime.now().isoformat(),
        languages=dict(lang_totals),
        detected_frameworks=all_frameworks,
        position_scores=scores,
    )

    response = map_pipeline_result(result)
    analysis_dict = response.model_dump()
    cache.analysis_result = analysis_dict

    # LLM が利用可能なら学習アドバイスも自動生成する
    advice, llm_failed = await _generate_advice_if_available(analysis_dict)
    cache.position_advice = advice

    # ステップ 5: DB 保存
    await set_progress(task_id, 5, _TOTAL_STEPS, "結果を保存中...")
    cache.status = "completed"
    cache.error_message = "LLM処理が利用できません" if llm_failed else None
    cache.completed_at = _now()
    db.commit()

    # ステップ 6: 完了
    await set_progress(task_id, 6, _TOTAL_STEPS, "完了")


async def _generate_advice_if_available(analysis: dict) -> tuple[str | None, bool]:
    """LLM が利用可能であれば学習アドバイスを生成する。

    戻り値は (advice, llm_failed) のタプル。
    llm_failed=True は LLM の呼び出しを試みたが失敗したことを示す。
    LLM が未設定またはスコア情報がない場合は llm_failed=False でスキップする。
    """
    from ...services.intelligence.llm_summarizer import generate_learning_advice

    try:
        llm_client = get_llm_client()
        if not await llm_client.check_available():
            logger.info("LLM が利用できないため学習アドバイスの生成をスキップしました")
            return None, False

        scores = analysis.get("position_scores")
        if not scores:
            return None, False

        advice = await generate_learning_advice(analysis, scores)
        if advice is None:
            logger.warning("LLM が学習アドバイスの生成に失敗しました")
            return None, True
        return advice, False
    except Exception:
        logger.warning("学習アドバイスの生成に失敗しましたが、分析結果は保存します", exc_info=True)
        return None, True


# ---------- ブログ AI サマリ ----------


async def _run_blog_summarize(db: Session, payload: dict) -> None:
    """ブログ記事の AI サマリを生成し、キャッシュに保存する。"""
    from ...services.intelligence.llm_summarizer import summarize_blog_articles

    user_id = payload["user_id"]
    cache = db.query(BlogSummaryCache).filter_by(user_id=user_id).first()
    if not cache:
        logger.error("ブログサマリキャッシュが見つかりません", extra={"user_id": user_id})
        return

    cache.status = "processing"
    cache.started_at = _now()
    db.commit()

    articles_data = payload.get("articles", [])
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
    db.commit()


# ---------- キャリアパス分析 ----------


async def _run_career_analysis(db: Session, payload: dict) -> None:
    """AI キャリアパス分析を実行し、結果を保存する。"""
    from ...services.career_analysis.builder import build_career_analysis

    user_id = payload["user_id"]
    record_id = payload["record_id"]
    target_position = payload["target_position"]

    analysis = db.query(CareerAnalysis).filter_by(id=record_id, user_id=user_id).first()
    if not analysis:
        logger.error("キャリア分析レコードが見つかりません", extra={"record_id": record_id})
        return

    analysis.status = "processing"
    analysis.started_at = _now()
    db.commit()

    llm_client = get_llm_client()
    try:
        result = await build_career_analysis(
            db=db,
            user_id=user_id,
            target_position=target_position,
            llm_client=llm_client,
        )
    except ValueError as exc:
        analysis.status = "dead_letter"
        analysis.error_message = str(exc)
        analysis.completed_at = _now()
        db.commit()
        raise exc

    analysis.result_json = json.dumps(result, ensure_ascii=False)
    analysis.status = "completed"
    analysis.error_message = None
    analysis.completed_at = _now()
    db.commit()


# ---------- 共通 ----------


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
    """タスク種別に応じた DB レコードを取得する。"""
    user_id = payload.get("user_id")
    if not user_id:
        return None
    if task_type == TaskType.GITHUB_ANALYSIS:
        return db.query(GitHubAnalysisCache).filter_by(user_id=user_id).first()
    if task_type == TaskType.BLOG_SUMMARIZE:
        return db.query(BlogSummaryCache).filter_by(user_id=user_id).first()
    if task_type == TaskType.CAREER_ANALYSIS:
        record_id = payload.get("record_id")
        if record_id:
            return db.query(CareerAnalysis).filter_by(id=record_id).first()
    return None


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
