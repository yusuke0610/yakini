"""worker タイムアウト・エラーハンドリングのテスト。

asyncio.TimeoutError を mock して、worker が適切なエラーステータスを設定するかを確認する。
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.models import BlogSummaryCache, GitHubAnalysisCache
from app.repositories import UserRepository
from app.services.tasks.worker import _run_blog_summarize, _run_github_analysis
from sqlalchemy.orm import Session


def _run(coro):
    """async 関数を同期的に実行するヘルパー。"""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# ── _run_github_analysis タイムアウトテスト ──────────────────────────────────


def test_github_analysis_timeout_propagates(db_session: Session) -> None:
    """collect_repos で asyncio.TimeoutError が発生した場合に例外が伝播することを確認する。

    _run_github_analysis は run_pipeline を呼ばず collect_repos を直接呼ぶため、
    パッチ対象は collect_repos が正しい。set_progress（Redis）もモックが必要。
    """
    user = UserRepository(db_session).create(
        "github:timeout-user",
        hashed_password=None,
        email="timeout@example.com",
    )
    cache = GitHubAnalysisCache(user_id=user.id, status="pending")
    db_session.add(cache)
    db_session.commit()

    with (
        patch(
            "app.services.intelligence.github_collector.collect_repos",
            new_callable=AsyncMock,
            side_effect=asyncio.TimeoutError,
        ),
        patch(
            "app.services.progress_service.set_progress",
            new_callable=AsyncMock,
        ),
    ):
        with pytest.raises(asyncio.TimeoutError):
            _run(
                _run_github_analysis(
                    db_session,
                    {
                        "user_id": user.id,
                        "github_username": "timeout-user",
                        "github_token": None,
                        "include_forks": False,
                    },
                )
            )

    db_session.refresh(cache)
    # _run_github_analysis はタイムアウトで例外を再 raise する
    # ステータスは processing のまま（_mark_dead_letter は execute_task 層が担う）
    assert cache.status == "processing"


def test_github_analysis_mark_dead_letter_on_unexpected_error(db_session: Session) -> None:
    """予期しないエラー発生時に _mark_dead_letter でステータスが dead_letter になることを確認する。"""
    from app.services.tasks.base import TaskType
    from app.services.tasks.worker import _mark_dead_letter

    user = UserRepository(db_session).create(
        "github:markfailed-user",
        hashed_password=None,
        email="markfailed@example.com",
    )
    cache = GitHubAnalysisCache(user_id=user.id, status="processing")
    db_session.add(cache)
    db_session.commit()

    _mark_dead_letter(
        db_session,
        TaskType.GITHUB_ANALYSIS,
        {"user_id": user.id},
    )

    db_session.refresh(cache)
    assert cache.status == "dead_letter"
    assert cache.error_message == "予期しないエラーが発生しました"


# ── _run_blog_summarize タイムアウトテスト ────────────────────────────────────


def test_blog_summarize_timeout_propagates(db_session: Session) -> None:
    """ブログサマリ生成で asyncio.TimeoutError が発生した場合に例外が伝播することを確認する。"""
    user = UserRepository(db_session).create(
        "blog-timeout-user",
        hashed_password=None,
        email="blogtimeout@example.com",
    )
    cache = BlogSummaryCache(user_id=user.id, status="pending")
    db_session.add(cache)
    db_session.commit()

    # LLM クライアントが利用可能であることをモック
    mock_llm = MagicMock()
    mock_llm.check_available = AsyncMock(return_value=True)

    with patch(
        "app.services.tasks.worker.get_llm_client",
        return_value=mock_llm,
    ):
        # ローカルインポートされる summarize_blog_articles を patch する
        with patch(
            "app.services.intelligence.llm_summarizer.summarize_blog_articles",
            new_callable=AsyncMock,
            side_effect=asyncio.TimeoutError,
        ):
            with pytest.raises(asyncio.TimeoutError):
                _run(
                    _run_blog_summarize(
                        db_session,
                        {"user_id": user.id, "articles": []},
                    )
                )

    db_session.refresh(cache)
    assert cache.status == "processing"


def test_blog_summarize_mark_dead_letter_on_unexpected_error(db_session: Session) -> None:
    """予期しないエラー発生時に _mark_dead_letter でブログサマリのステータスが dead_letter になることを確認する。"""
    from app.services.tasks.base import TaskType
    from app.services.tasks.worker import _mark_dead_letter

    user = UserRepository(db_session).create(
        "blog-markfailed-user",
        hashed_password=None,
        email="blogmarkfailed@example.com",
    )
    cache = BlogSummaryCache(user_id=user.id, status="processing")
    db_session.add(cache)
    db_session.commit()

    _mark_dead_letter(
        db_session,
        TaskType.BLOG_SUMMARIZE,
        {"user_id": user.id},
    )

    db_session.refresh(cache)
    assert cache.status == "dead_letter"
    assert cache.error_message == "予期しないエラーが発生しました"
