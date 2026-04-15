"""バックグラウンドタスクのワーカー。

ローカル: BackgroundTasks から直接呼ばれる。
Cloud: /internal/tasks/{type} エンドポイント経由で呼ばれる。
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

logger = get_logger(__name__)


# duration_ms がこの閾値を超えたら WARNING を出す（5分）
_SLOW_TASK_THRESHOLD_MS = 300_000



async def execute_task(task_type: TaskType, payload: dict) -> None:
    """タスクを実行する。自前で DB セッションを作成・管理する。"""
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
    except Exception:
        duration_ms = int((time.monotonic() - start) * 1000)
        logger.error(
            "タスク実行に失敗しました",
            extra={
                "task_id": task_type.value,
                "user_id": user_id,
                "record_id": record_id,
                "status": "failed",
                "error_type": type(Exception).__name__,
                "duration_ms": duration_ms,
            },
            exc_info=True,
        )
        _mark_failed(db, task_type, payload)
        if isinstance(user_id, str) and user_id != "unknown":
            _create_notification(db, task_type, user_id, "failed")
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
        cache.status = "failed"
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

    # ステップ 4: スコア算出
    await set_progress(task_id, 4, _TOTAL_STEPS, "スコア算出中...")
    scores = calculate_position_scores(repos)

    result = IntelligenceResult(
        username=payload["github_username"],
        repos_analyzed=extraction.repos_analyzed,
        unique_skills=len(extraction.unique_skills),
        analyzed_at=datetime.now().isoformat(),
        languages=dict(lang_totals),
        position_scores=scores,
    )

    response = map_pipeline_result(result)
    analysis_dict = response.model_dump()
    cache.analysis_result = analysis_dict

    # LLM が利用可能なら学習アドバイスも自動生成する
    advice = await _generate_advice_if_available(analysis_dict)
    cache.position_advice = advice

    # ステップ 5: DB 保存
    await set_progress(task_id, 5, _TOTAL_STEPS, "結果を保存中...")
    cache.status = "completed"
    cache.error_message = None
    cache.completed_at = _now()
    db.commit()

    # ステップ 6: 完了
    await set_progress(task_id, 6, _TOTAL_STEPS, "完了")


async def _generate_advice_if_available(analysis: dict) -> str | None:
    """LLM が利用可能であれば学習アドバイスを生成する。失敗時は None を返す。"""
    from ...services.intelligence.llm_summarizer import generate_learning_advice

    try:
        llm_client = get_llm_client()
        if not await llm_client.check_available():
            logger.info("LLM が利用できないため学習アドバイスの生成をスキップしました")
            return None

        scores = analysis.get("position_scores")
        if not scores:
            return None

        advice = await generate_learning_advice(analysis, scores)
        return advice if advice else None
    except Exception:
        logger.warning("学習アドバイスの生成に失敗しましたが、分析結果は保存します", exc_info=True)
        return None


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
        cache.status = "failed"
        cache.error_message = "LLM サービスが利用できません"
        cache.completed_at = _now()
        db.commit()
        return

    summary = await summarize_blog_articles(articles_data)
    if not summary:
        cache.status = "failed"
        cache.error_message = "AI サマリの生成に失敗しました"
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
        analysis.status = "failed"
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


def _mark_failed(db: Session, task_type: TaskType, payload: dict) -> None:
    """タスク失敗時にステータスを更新する（予期しないエラー用）。"""
    try:
        user_id = payload.get("user_id")
        if not user_id:
            return

        now = _now()

        if task_type == TaskType.GITHUB_ANALYSIS:
            cache = db.query(GitHubAnalysisCache).filter_by(user_id=user_id).first()
            if cache and cache.status != "completed":
                cache.status = "failed"
                cache.error_message = "予期しないエラーが発生しました"
                cache.completed_at = now
                db.commit()

        elif task_type == TaskType.BLOG_SUMMARIZE:
            cache = db.query(BlogSummaryCache).filter_by(user_id=user_id).first()
            if cache and cache.status != "completed":
                cache.status = "failed"
                cache.error_message = "予期しないエラーが発生しました"
                cache.completed_at = now
                db.commit()

        elif task_type == TaskType.CAREER_ANALYSIS:
            record_id = payload.get("record_id")
            if record_id:
                analysis = db.query(CareerAnalysis).filter_by(id=record_id).first()
                if analysis and analysis.status != "completed":
                    analysis.status = "failed"
                    analysis.error_message = "予期しないエラーが発生しました"
                    analysis.completed_at = now
                    db.commit()
    except Exception:
        logger.exception("タスク失敗マーク中にエラーが発生しました")
