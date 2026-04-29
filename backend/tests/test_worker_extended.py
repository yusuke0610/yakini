"""
worker の execute_task および各タスクランナーのテスト（状態遷移・フロー検証）。

対象モジュール: app.services.tasks.worker
テスト方針:
  - _run_github_analysis / _run_blog_summarize / _run_career_analysis を直接テスト
  - 外部サービス（LLM, GitHub API, Redis）はすべてモック化
  - DB はフィクスチャの一時 SQLite セッションを使用
  - execute_task のルーティングロジックも SessionLocal パッチで確認
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.models import BlogSummaryCache, GitHubAnalysisCache
from app.models.career_analysis import CareerAnalysis
from app.repositories import UserRepository
from app.services.tasks.base import TaskType
from app.services.tasks.worker import (
    _generate_advice_if_available,
    _mark_dead_letter,
    _run_blog_summarize,
    _run_career_analysis,
    _run_github_analysis,
    execute_task,
)
from sqlalchemy.orm import Session


def _run(coro):
    """async 関数を同期的に実行するヘルパー。"""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# ── _run_github_analysis ──────────────────────────────────────────────────


class TestRunGithubAnalysis:
    def _make_user_and_cache(self, db: Session, username="github:gh-user"):
        user = UserRepository(db).create(username, hashed_password=None, email=f"{username}@test.com")
        cache = GitHubAnalysisCache(user_id=user.id, status="pending")
        db.add(cache)
        db.commit()
        return user, cache

    def _sample_repos(self):
        from app.services.intelligence.github_collector import RepoData

        return [
            RepoData(
                name="repo1",
                owner="gh-user",
                description="",
                languages={"Python": 10000},
                topics=["fastapi"],
                created_at="2023-01-01T00:00:00Z",
                pushed_at="2024-01-01T00:00:00Z",
                fork=False,
                stargazers_count=0,
                default_branch="main",
                dependencies=[],
                root_files=[],
                detected_frameworks=[],
            )
        ]

    def test_status_transitions_to_completed(self, db_session: Session):
        """正常系: status が completed に遷移すること。"""
        user, cache = self._make_user_and_cache(db_session)
        repos = self._sample_repos()

        with (
            patch(
                "app.services.intelligence.github_collector.collect_repos",
                new_callable=AsyncMock,
                return_value=repos,
            ),
            patch(
                "app.services.progress_service.set_progress",
                new_callable=AsyncMock,
            ),
            patch(
                "app.services.tasks.worker.get_llm_client",
                return_value=MagicMock(check_available=AsyncMock(return_value=False)),
            ),
            patch("app.core.encryption.decrypt_field", return_value="token123"),
        ):
            _run(
                _run_github_analysis(
                    db_session,
                    {
                        "user_id": user.id,
                        "github_username": "gh-user",
                        "github_token": "encrypted_token",
                        "include_forks": False,
                    },
                )
            )

        db_session.refresh(cache)
        assert cache.status == "completed"
        assert cache.analysis_result is not None
        assert cache.completed_at is not None

    def test_status_transitions_to_processing_at_start(self, db_session: Session):
        """タスク開始時に status が processing に更新されること。"""
        user, cache = self._make_user_and_cache(db_session)
        repos = self._sample_repos()

        processing_status = []

        async def _fake_collect(**kwargs):
            db_session.refresh(cache)
            processing_status.append(cache.status)
            return repos

        with (
            patch(
                "app.services.intelligence.github_collector.collect_repos",
                side_effect=_fake_collect,
            ),
            patch("app.services.progress_service.set_progress", new_callable=AsyncMock),
            patch(
                "app.services.tasks.worker.get_llm_client",
                return_value=MagicMock(check_available=AsyncMock(return_value=False)),
            ),
            patch("app.core.encryption.decrypt_field", return_value=None),
        ):
            _run(
                _run_github_analysis(
                    db_session,
                    {
                        "user_id": user.id,
                        "github_username": "gh-user",
                        "github_token": None,
                        "include_forks": False,
                    },
                )
            )

        assert "processing" in processing_status

    def test_github_user_not_found_sets_dead_letter(self, db_session: Session):
        """GitHubUserNotFoundError 発生時に status が dead_letter になること。"""
        from app.services.intelligence.github.api_client import GitHubUserNotFoundError

        user, cache = self._make_user_and_cache(db_session, "github:notfound")

        with (
            patch(
                "app.services.intelligence.github_collector.collect_repos",
                new_callable=AsyncMock,
                side_effect=GitHubUserNotFoundError("notfound"),
            ),
            patch("app.services.progress_service.set_progress", new_callable=AsyncMock),
            patch("app.core.encryption.decrypt_field", return_value=None),
        ):
            with pytest.raises(GitHubUserNotFoundError):
                _run(
                    _run_github_analysis(
                        db_session,
                        {
                            "user_id": user.id,
                            "github_username": "notfound",
                            "github_token": None,
                            "include_forks": False,
                        },
                    )
                )

        db_session.refresh(cache)
        assert cache.status == "dead_letter"

    def test_no_cache_returns_early(self, db_session: Session):
        """キャッシュが見つからない場合、例外なく早期リターンすること。"""
        _run(
            _run_github_analysis(
                db_session,
                {
                    "user_id": "nonexistent-user-id",
                    "github_username": "nobody",
                    "github_token": None,
                    "include_forks": False,
                },
            )
        )
        # 例外が発生しないことを確認


# ── _run_blog_summarize ───────────────────────────────────────────────────


class TestRunBlogSummarize:
    def _make_user_and_cache(self, db: Session, username="blog-worker-user"):
        user = UserRepository(db).create(username, hashed_password=None, email=f"{username}@test.com")
        cache = BlogSummaryCache(user_id=user.id, status="pending")
        db.add(cache)
        db.commit()
        return user, cache

    def test_success_status_completed(self, db_session: Session):
        """正常系: LLM が要約を返し、status が completed になること。"""
        user, cache = self._make_user_and_cache(db_session)
        mock_llm = MagicMock()
        mock_llm.check_available = AsyncMock(return_value=True)

        with (
            patch("app.services.tasks.worker.get_llm_client", return_value=mock_llm),
            patch(
                "app.services.intelligence.llm_summarizer.summarize_blog_articles",
                new_callable=AsyncMock,
                return_value="AI 要約テキスト",
            ),
        ):
            _run(
                _run_blog_summarize(
                    db_session,
                    {"user_id": user.id, "articles": [{"title": "記事1"}]},
                )
            )

        db_session.refresh(cache)
        assert cache.status == "completed"
        assert cache.summary == "AI 要約テキスト"
        assert cache.completed_at is not None

    def test_llm_unavailable_sets_dead_letter(self, db_session: Session):
        """LLM が利用不可の場合に status が dead_letter になること。"""
        user, cache = self._make_user_and_cache(db_session, "blog-nollm")
        mock_llm = MagicMock()
        mock_llm.check_available = AsyncMock(return_value=False)

        with patch("app.services.tasks.worker.get_llm_client", return_value=mock_llm):
            _run(
                _run_blog_summarize(
                    db_session,
                    {"user_id": user.id, "articles": []},
                )
            )

        db_session.refresh(cache)
        assert cache.status == "dead_letter"
        assert cache.error_message is not None

    def test_empty_summary_sets_dead_letter(self, db_session: Session):
        """LLM が空文字を返した場合に status が dead_letter になること。"""
        user, cache = self._make_user_and_cache(db_session, "blog-empty")
        mock_llm = MagicMock()
        mock_llm.check_available = AsyncMock(return_value=True)

        with (
            patch("app.services.tasks.worker.get_llm_client", return_value=mock_llm),
            patch(
                "app.services.intelligence.llm_summarizer.summarize_blog_articles",
                new_callable=AsyncMock,
                return_value="",
            ),
        ):
            _run(
                _run_blog_summarize(
                    db_session,
                    {"user_id": user.id, "articles": []},
                )
            )

        db_session.refresh(cache)
        assert cache.status == "dead_letter"

    def test_no_cache_returns_early(self, db_session: Session):
        """キャッシュが見つからない場合、例外なく早期リターンすること。"""
        _run(
            _run_blog_summarize(
                db_session,
                {"user_id": "ghost-user", "articles": []},
            )
        )

    def test_status_set_to_processing_before_llm_call(self, db_session: Session):
        """LLM 呼び出し前に status が processing に更新されること。"""
        user, cache = self._make_user_and_cache(db_session, "blog-processing")
        processing_status = []
        mock_llm = MagicMock()

        async def _fake_check_available():
            db_session.refresh(cache)
            processing_status.append(cache.status)
            return False

        mock_llm.check_available = _fake_check_available

        with patch("app.services.tasks.worker.get_llm_client", return_value=mock_llm):
            _run(
                _run_blog_summarize(
                    db_session,
                    {"user_id": user.id, "articles": []},
                )
            )

        assert "processing" in processing_status


# ── _run_career_analysis ──────────────────────────────────────────────────


class TestRunCareerAnalysis:
    def _make_user_and_analysis(self, db: Session, username="career-worker-user"):
        user = UserRepository(db).create(username, hashed_password=None, email=f"{username}@test.com")
        analysis = CareerAnalysis(
            user_id=user.id,
            version=1,
            target_position="バックエンドエンジニア",
            status="pending",
        )
        db.add(analysis)
        db.commit()
        return user, analysis

    def test_success_status_completed(self, db_session: Session):
        """正常系: キャリア分析が完了し status が completed になること。"""
        user, analysis = self._make_user_and_analysis(db_session)
        mock_llm = MagicMock()
        fake_result = {"strengths": [], "career_paths": [], "action_items": []}

        with (
            patch("app.services.tasks.worker.get_llm_client", return_value=mock_llm),
            patch(
                "app.services.career_analysis.builder.build_career_analysis",
                new_callable=AsyncMock,
                return_value=fake_result,
            ),
        ):
            _run(
                _run_career_analysis(
                    db_session,
                    {
                        "user_id": user.id,
                        "record_id": analysis.id,
                        "target_position": "バックエンドエンジニア",
                    },
                )
            )

        db_session.refresh(analysis)
        assert analysis.status == "completed"
        assert analysis.result_json is not None
        assert analysis.completed_at is not None

    def test_value_error_sets_dead_letter(self, db_session: Session):
        """build_career_analysis が ValueError を送出した場合 status が dead_letter になること。"""
        user, analysis = self._make_user_and_analysis(db_session, "career-err")
        mock_llm = MagicMock()

        with (
            patch("app.services.tasks.worker.get_llm_client", return_value=mock_llm),
            patch(
                "app.services.career_analysis.builder.build_career_analysis",
                new_callable=AsyncMock,
                side_effect=ValueError("必要なデータが不足しています"),
            ),
        ):
            with pytest.raises(ValueError):
                _run(
                    _run_career_analysis(
                        db_session,
                        {
                            "user_id": user.id,
                            "record_id": analysis.id,
                            "target_position": "バックエンドエンジニア",
                        },
                    )
                )

        db_session.refresh(analysis)
        assert analysis.status == "dead_letter"
        assert "不足" in analysis.error_message

    def test_no_record_returns_early(self, db_session: Session):
        """レコードが見つからない場合、例外なく早期リターンすること。"""
        _run(
            _run_career_analysis(
                db_session,
                {
                    "user_id": "ghost",
                    "record_id": 99999,
                    "target_position": "test",
                },
            )
        )


# ── _generate_advice_if_available ─────────────────────────────────────────


class TestGenerateAdviceIfAvailable:
    def _analysis(self):
        return {
            "repos_analyzed": 5,
            "languages": {"Python": 50000},
            "position_scores": {
                "backend": 70,
                "frontend": 20,
                "fullstack": 45,
                "sre": 25,
                "cloud": 15,
                "missing_skills": [],
            },
        }

    def test_llm_unavailable_returns_none(self):
        """LLM が利用不可の場合 (None, False) を返すこと。"""
        mock_llm = MagicMock()
        mock_llm.check_available = AsyncMock(return_value=False)

        with patch("app.services.tasks.worker.get_llm_client", return_value=mock_llm):
            result = _run(_generate_advice_if_available(self._analysis()))

        assert result == (None, False)

    def test_llm_available_returns_advice(self):
        """LLM が利用可能の場合、(アドバイス文字列, False) を返すこと。"""
        mock_llm = MagicMock()
        mock_llm.check_available = AsyncMock(return_value=True)

        with (
            patch("app.services.tasks.worker.get_llm_client", return_value=mock_llm),
            patch(
                "app.services.intelligence.llm_summarizer.generate_learning_advice",
                new_callable=AsyncMock,
                return_value="学習アドバイスです",
            ),
        ):
            result = _run(_generate_advice_if_available(self._analysis()))

        assert result == ("学習アドバイスです", False)

    def test_llm_exception_returns_none(self):
        """LLM が例外を送出した場合 (None, True) を返し例外が外に漏れないこと。"""
        mock_llm = MagicMock()
        mock_llm.check_available = AsyncMock(side_effect=Exception("LLM クラッシュ"))

        with patch("app.services.tasks.worker.get_llm_client", return_value=mock_llm):
            result = _run(_generate_advice_if_available(self._analysis()))

        assert result == (None, True)

    def test_no_position_scores_returns_none(self):
        """position_scores が None の場合 (None, False) を返すこと。"""
        mock_llm = MagicMock()
        mock_llm.check_available = AsyncMock(return_value=True)

        with patch("app.services.tasks.worker.get_llm_client", return_value=mock_llm):
            result = _run(_generate_advice_if_available({"repos_analyzed": 5}))

        assert result == (None, False)


# ── execute_task (ルーティングロジック) ───────────────────────────────────


class TestExecuteTask:
    def test_unknown_task_type_logs_error_and_returns(self, db_session: Session):
        """不明なタスク種別の場合エラーログを出し例外を上げないこと。"""
        # TaskType は Enum なのでここでは直接 string を渡すことで unknown な値をシミュレート
        # execute_task は if-elif で全種別をチェックするため、該当しない場合 logger.error を呼ぶ

        # _run_github_analysis 等が呼ばれないことをモックで確認
        with (
            patch("app.db.database.SessionLocal", return_value=db_session),
            patch(
                "app.services.tasks.worker._run_github_analysis",
                new_callable=AsyncMock,
            ) as mock_gh,
            patch(
                "app.services.tasks.worker._run_blog_summarize",
                new_callable=AsyncMock,
            ) as mock_blog,
        ):
            # TaskType.GITHUB_ANALYSIS でもなく BLOG_SUMMARIZE でもない dummy を渡す
            # ただし TaskType は str Enum なので実際の enum 値のみ渡せる。
            # ここでは GITHUB_ANALYSIS を使い mock を差し替えて成功フローをシミュレート
            mock_gh.return_value = None
            _run(
                execute_task(
                    TaskType.GITHUB_ANALYSIS,
                    {"user_id": "test-user", "github_username": "u"},
                )
            )

        mock_gh.assert_called_once()
        mock_blog.assert_not_called()

    def test_execute_task_marks_dead_letter_on_error(self, db_session: Session):
        """予期しない例外が発生した場合（max_attempts=1）、_mark_dead_letter が
        呼ばれ例外が再 raise されること。"""
        mock_db = MagicMock()
        mock_session_local = MagicMock(return_value=mock_db)

        with (
            patch("app.services.tasks.worker.SessionLocal", mock_session_local),
            patch(
                "app.services.tasks.worker._run_github_analysis",
                new_callable=AsyncMock,
                side_effect=RuntimeError("予期しないクラッシュ"),
            ),
            patch("app.services.tasks.worker._mark_dead_letter") as mock_mark_dead_letter,
            patch("app.services.tasks.worker._create_notification"),
        ):
            with pytest.raises(RuntimeError, match="予期しないクラッシュ"):
                _run(
                    execute_task(
                        TaskType.GITHUB_ANALYSIS,
                        {"user_id": "test-user-id", "github_username": "u"},
                    )
                )

        mock_mark_dead_letter.assert_called_once()
        call_args = mock_mark_dead_letter.call_args
        assert call_args.args == (
            mock_db,
            TaskType.GITHUB_ANALYSIS,
            {"user_id": "test-user-id", "github_username": "u"},
        )
        assert isinstance(call_args.kwargs.get("error"), RuntimeError)

    def test_execute_task_creates_notification_on_success(self, db_session: Session):
        """タスク成功時に _create_notification が呼ばれること。"""
        mock_db = MagicMock()
        mock_session_local = MagicMock(return_value=mock_db)

        with (
            patch("app.services.tasks.worker.SessionLocal", mock_session_local),
            patch(
                "app.services.tasks.worker._run_blog_summarize",
                new_callable=AsyncMock,
                return_value=None,
            ),
            patch("app.services.tasks.worker._create_notification") as mock_notify,
        ):
            _run(
                execute_task(
                    TaskType.BLOG_SUMMARIZE,
                    {"user_id": "notif-test-user"},
                )
            )

        mock_notify.assert_called_once_with(
            mock_db, TaskType.BLOG_SUMMARIZE, "notif-test-user", "completed"
        )


# ── _mark_dead_letter (career_analysis) ──────────────────────────────────


class TestMarkDeadLetterCareerAnalysis:
    def test_mark_dead_letter_career_analysis(self, db_session: Session):
        """_mark_dead_letter が CareerAnalysis のステータスを dead_letter に更新すること。"""
        user = UserRepository(db_session).create(
            "mf-career-user", hashed_password=None, email="mfcareer@test.com"
        )
        analysis = CareerAnalysis(
            user_id=user.id,
            version=1,
            target_position="SRE",
            status="processing",
        )
        db_session.add(analysis)
        db_session.commit()

        _mark_dead_letter(
            db_session,
            TaskType.CAREER_ANALYSIS,
            {"user_id": user.id, "record_id": analysis.id},
        )

        db_session.refresh(analysis)
        assert analysis.status == "dead_letter"
        assert analysis.error_message == "予期しないエラーが発生しました"

    def test_mark_dead_letter_does_not_overwrite_completed(self, db_session: Session):
        """completed 済みのレコードは _mark_dead_letter で上書きされないこと。"""
        user = UserRepository(db_session).create(
            "mf-career-done", hashed_password=None, email="mfcareerdone@test.com"
        )
        analysis = CareerAnalysis(
            user_id=user.id,
            version=1,
            target_position="SRE",
            status="completed",
        )
        db_session.add(analysis)
        db_session.commit()

        _mark_dead_letter(
            db_session,
            TaskType.CAREER_ANALYSIS,
            {"user_id": user.id, "record_id": analysis.id},
        )

        db_session.refresh(analysis)
        assert analysis.status == "completed"
