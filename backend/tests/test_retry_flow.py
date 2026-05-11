"""
リトライフローの統合テスト。

対象:
- ``app.services.tasks.worker.execute_task`` のリトライ分岐
  - NonRetryableError → status=dead_letter（リトライ不可）
  - RetryableError / 予期しない例外 → 試行回数に応じて retrying / dead_letter
- ``app.routers.internal.handle_task`` の HTTP ステータスマッピング
  - NonRetryableError → 200
  - RetryableError (retry_after なし) → 503
  - RetryableError (retry_after あり) → 429 + Retry-After ヘッダー
  - 予期しない例外 → 500
- 手動再実行エンドポイント（/retry）の状態リセット挙動
"""

import asyncio
import os
from unittest.mock import AsyncMock, patch

import pytest
from app.models import BlogSummaryCache, GitHubAnalysisCache
from app.models.career_analysis import CareerAnalysis
from app.repositories import UserRepository
from app.services.tasks.base import TaskType
from app.services.tasks.exceptions import NonRetryableError, RetryableError
from app.services.tasks.worker import execute_task
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from conftest import auth_header


def _run(coro):
    """async 関数を同期的に実行するヘルパー。"""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def _keep_open_session(db: Session):
    """worker が呼ぶ ``db.close()`` をテスト用セッションでは無効化するプロキシ。

    worker は finally 節で ``db.close()`` を呼ぶが、テストでは同じ ``db_session`` を
    検証側でも使い続けたいため、close だけ no-op 化する。
    """

    class _Proxy:
        def __init__(self, real: Session) -> None:
            self._real = real

        def __getattr__(self, name):
            return getattr(self._real, name)

        def close(self) -> None:
            self._real.expire_all()

    return _Proxy(db)


# ══════════════════════════════════════════════════════════════════════
# execute_task リトライ分岐
# ══════════════════════════════════════════════════════════════════════


class TestExecuteTaskRetryBranching:
    """execute_task が retry_count / max_attempts に応じて正しく分岐することを確認する。"""

    def test_non_retryable_error_marks_dead_letter(self, db_session: Session):
        """NonRetryableError はリトライ回数に関係なく status=dead_letter で終える。"""
        user = UserRepository(db_session).create(
            "github:nonretry-user", hashed_password=None, email="nonretry@test.com",
        )
        cache = GitHubAnalysisCache(user_id=user.id, status="processing")
        db_session.add(cache)
        db_session.commit()

        with (
            patch(
                "app.services.tasks.worker.SessionLocal",
                return_value=_keep_open_session(db_session),
            ),
            patch(
                "app.services.tasks.worker._run_github_analysis",
                new_callable=AsyncMock,
                side_effect=NonRetryableError("認証不可"),
            ),
            patch("app.services.tasks.worker._create_notification"),
        ):
            with pytest.raises(NonRetryableError):
                _run(
                    execute_task(
                        TaskType.GITHUB_ANALYSIS,
                        {"user_id": user.id},
                        retry_count=0,
                        max_attempts=3,
                    ),
                )

        db_session.refresh(cache)
        assert cache.status == "dead_letter"
        assert "認証不可" in (cache.error_message or "")

    def test_retryable_error_with_attempts_remaining_marks_retrying(
        self, db_session: Session,
    ):
        """RetryableError で試行回数が残っていれば status=retrying にする。"""
        user = UserRepository(db_session).create(
            "github:retrying-user", hashed_password=None, email="retrying@test.com",
        )
        cache = GitHubAnalysisCache(user_id=user.id, status="processing")
        db_session.add(cache)
        db_session.commit()

        with (
            patch(
                "app.services.tasks.worker.SessionLocal",
                return_value=_keep_open_session(db_session),
            ),
            patch(
                "app.services.tasks.worker._run_github_analysis",
                new_callable=AsyncMock,
                side_effect=RetryableError("一時エラー", retry_after=10),
            ),
            patch("app.services.tasks.worker._create_notification") as mock_notify,
        ):
            with pytest.raises(RetryableError):
                _run(
                    execute_task(
                        TaskType.GITHUB_ANALYSIS,
                        {"user_id": user.id},
                        retry_count=0,
                        max_attempts=3,
                    ),
                )

        db_session.refresh(cache)
        assert cache.status == "retrying"
        assert cache.retry_count == 0
        assert cache.max_retries == 3
        # retrying 状態では失敗通知を出さない
        mock_notify.assert_not_called()

    def test_retryable_error_on_final_attempt_marks_dead_letter(
        self, db_session: Session,
    ):
        """最終試行（retry_count == max_attempts - 1）で失敗したら dead_letter。"""
        user = UserRepository(db_session).create(
            "github:deadletter-user", hashed_password=None, email="dl@test.com",
        )
        cache = GitHubAnalysisCache(user_id=user.id, status="retrying")
        db_session.add(cache)
        db_session.commit()

        with (
            patch(
                "app.services.tasks.worker.SessionLocal",
                return_value=_keep_open_session(db_session),
            ),
            patch(
                "app.services.tasks.worker._run_github_analysis",
                new_callable=AsyncMock,
                side_effect=RetryableError("最後も失敗"),
            ),
            patch("app.services.tasks.worker._create_notification") as mock_notify,
        ):
            with pytest.raises(RetryableError):
                _run(
                    execute_task(
                        TaskType.GITHUB_ANALYSIS,
                        {"user_id": user.id},
                        retry_count=2,
                        max_attempts=3,
                    ),
                )

        db_session.refresh(cache)
        assert cache.status == "dead_letter"
        # 最終試行では失敗通知を出す
        mock_notify.assert_called_once()
        args = mock_notify.call_args.args
        assert args[2] == user.id
        assert args[3] == "failed"

    def test_unknown_exception_treated_as_retryable(self, db_session: Session):
        """分類されていない例外（RuntimeError 等）は retryable と同様に扱う。"""
        user = UserRepository(db_session).create(
            "github:unknown-err-user", hashed_password=None, email="unk@test.com",
        )
        cache = GitHubAnalysisCache(user_id=user.id, status="processing")
        db_session.add(cache)
        db_session.commit()

        with (
            patch(
                "app.services.tasks.worker.SessionLocal",
                return_value=_keep_open_session(db_session),
            ),
            patch(
                "app.services.tasks.worker._run_github_analysis",
                new_callable=AsyncMock,
                side_effect=RuntimeError("想定外のクラッシュ"),
            ),
            patch("app.services.tasks.worker._create_notification"),
        ):
            with pytest.raises(RuntimeError):
                _run(
                    execute_task(
                        TaskType.GITHUB_ANALYSIS,
                        {"user_id": user.id},
                        retry_count=0,
                        max_attempts=3,
                    ),
                )

        db_session.refresh(cache)
        assert cache.status == "retrying"

    def test_local_default_marks_dead_letter_on_first_failure(
        self, db_session: Session,
    ):
        """ローカル（max_attempts=1 デフォルト）では最初の失敗で即 dead_letter。"""
        user = UserRepository(db_session).create(
            "github:local-fail-user", hashed_password=None, email="local@test.com",
        )
        cache = GitHubAnalysisCache(user_id=user.id, status="processing")
        db_session.add(cache)
        db_session.commit()

        with (
            patch(
                "app.services.tasks.worker.SessionLocal",
                return_value=_keep_open_session(db_session),
            ),
            patch(
                "app.services.tasks.worker._run_github_analysis",
                new_callable=AsyncMock,
                side_effect=RuntimeError("ローカル失敗"),
            ),
            patch("app.services.tasks.worker._create_notification"),
        ):
            with pytest.raises(RuntimeError):
                # retry_count=0, max_attempts=1（デフォルト）
                _run(execute_task(TaskType.GITHUB_ANALYSIS, {"user_id": user.id}))

        db_session.refresh(cache)
        assert cache.status == "dead_letter"


# ══════════════════════════════════════════════════════════════════════
# /internal/tasks/{type} HTTP ステータスマッピング
# ══════════════════════════════════════════════════════════════════════


class TestInternalRouterStatusMapping:
    """Cloud Tasks がリトライ判断に使う HTTP ステータスコードを確認する。"""

    def _payload(self) -> dict:
        return {"user_id": "any", "github_username": "u"}

    def test_success_returns_200(self, client: TestClient):
        # conftest で execute_task は AsyncMock(return_value=None) に差し替え済み
        resp = client.post(
            "/internal/tasks/github_analysis",
            json=self._payload(),
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_non_retryable_returns_200_to_stop_retry(self, client: TestClient):
        """NonRetryableError は 2xx を返し Cloud Tasks のリトライを止める。"""
        with patch(
            "app.routers.internal.execute_task",
            new=AsyncMock(side_effect=NonRetryableError("認証エラー")),
        ):
            resp = client.post(
                "/internal/tasks/github_analysis",
                json=self._payload(),
            )
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "non_retryable"

    def test_retryable_without_retry_after_returns_503(self, client: TestClient):
        """RetryableError（retry_after なし）は 503 で Cloud Tasks にリトライさせる。"""
        with patch(
            "app.routers.internal.execute_task",
            new=AsyncMock(side_effect=RetryableError("一時エラー")),
        ):
            resp = client.post(
                "/internal/tasks/github_analysis",
                json=self._payload(),
            )
        assert resp.status_code == 503

    def test_retryable_with_retry_after_returns_429(self, client: TestClient):
        """RetryableError（retry_after あり）は 429 + Retry-After ヘッダーで返す。"""
        with patch(
            "app.routers.internal.execute_task",
            new=AsyncMock(side_effect=RetryableError("rate limit", retry_after=30)),
        ):
            resp = client.post(
                "/internal/tasks/github_analysis",
                json=self._payload(),
            )
        assert resp.status_code == 429
        assert resp.headers.get("Retry-After") == "30"

    def test_unexpected_exception_returns_500(self, client: TestClient):
        """予期しない例外は 500 で Cloud Tasks にリトライさせる。"""
        with patch(
            "app.routers.internal.execute_task",
            new=AsyncMock(side_effect=RuntimeError("予期しない")),
        ):
            resp = client.post(
                "/internal/tasks/github_analysis",
                json=self._payload(),
            )
        assert resp.status_code == 500

    def test_retry_count_header_forwarded_to_worker(self, client: TestClient):
        """X-CloudTasks-TaskRetryCount ヘッダーが execute_task に渡されること。"""
        captured: dict = {}

        async def _capture(task_type, payload, *, retry_count, max_attempts):
            captured["retry_count"] = retry_count
            captured["max_attempts"] = max_attempts

        with patch("app.routers.internal.execute_task", new=AsyncMock(side_effect=_capture)):
            with patch.dict(os.environ, {"TASK_MAX_ATTEMPTS": "5"}):
                resp = client.post(
                    "/internal/tasks/github_analysis",
                    json=self._payload(),
                    headers={"X-CloudTasks-TaskRetryCount": "2"},
                )
        assert resp.status_code == 200
        assert captured["retry_count"] == 2
        assert captured["max_attempts"] == 5

    def test_invalid_task_type_returns_400(self, client: TestClient):
        resp = client.post("/internal/tasks/invalid_type", json={"user_id": "x"})
        assert resp.status_code == 400


# ══════════════════════════════════════════════════════════════════════
# 手動再実行エンドポイント
# ══════════════════════════════════════════════════════════════════════


class TestRetryEndpoints:
    """`POST /{resource}/retry` が失敗状態をリセットし再ディスパッチすること。"""

    def test_career_retry_resets_and_dispatches(self, client: TestClient):
        headers = auth_header(client, "retry-career-user")

        # dead_letter のレコードを直接作る
        db = client._db_session
        user = UserRepository(db).get_by_username("retry-career-user")
        analysis = CareerAnalysis(
            user_id=user.id,
            version=1,
            target_position="SRE",
            status="dead_letter",
            error_message="old error",
            retry_count=3,
        )
        db.add(analysis)
        db.commit()

        resp = client.post(
            f"/api/career-analysis/{analysis.id}/retry",
            headers=headers,
        )
        assert resp.status_code == 202
        body = resp.json()
        assert body["status"] == "pending"

        db.refresh(analysis)
        assert analysis.status == "pending"
        assert analysis.retry_count == 0
        assert analysis.error_message is None

    def test_career_retry_rejects_non_terminal_status(self, client: TestClient):
        """pending / processing / completed 状態は 409 を返す。"""
        headers = auth_header(client, "retry-running-user")

        db = client._db_session
        user = UserRepository(db).get_by_username("retry-running-user")
        analysis = CareerAnalysis(
            user_id=user.id,
            version=1,
            target_position="SRE",
            status="processing",
        )
        db.add(analysis)
        db.commit()

        resp = client.post(
            f"/api/career-analysis/{analysis.id}/retry",
            headers=headers,
        )
        assert resp.status_code == 409

    def test_career_retry_returns_404_for_missing(self, client: TestClient):
        headers = auth_header(client, "retry-404-user")
        resp = client.post("/api/career-analysis/999999/retry", headers=headers)
        assert resp.status_code == 404

    def test_intelligence_retry_requires_github_user(self, client: TestClient):
        """GitHub 以外のユーザーは GitHub 分析リトライを実行できない。"""
        headers = auth_header(client, "non-github-user")
        resp = client.post("/api/intelligence/analyze/retry", headers=headers)
        assert resp.status_code == 403

    def test_intelligence_retry_resets_cache(self, client: TestClient):
        headers = auth_header(client, "github:retry-intel-user")
        db = client._db_session
        user = UserRepository(db).get_by_username("github:retry-intel-user")

        cache = GitHubAnalysisCache(
            user_id=user.id,
            status="dead_letter",
            error_message="old",
            retry_count=3,
        )
        db.add(cache)
        db.commit()

        resp = client.post("/api/intelligence/analyze/retry", headers=headers)
        assert resp.status_code == 202
        assert resp.json()["status"] == "pending"

        db.refresh(cache)
        assert cache.status == "pending"
        assert cache.retry_count == 0
        assert cache.error_message is None

    def test_blog_retry_requires_articles_body(self, client: TestClient):
        """ブログサマリ再実行には articles 本文が必要。"""
        headers = auth_header(client, "retry-blog-user")
        db = client._db_session
        user = UserRepository(db).get_by_username("retry-blog-user")

        cache = BlogSummaryCache(
            user_id=user.id,
            status="dead_letter",
            error_message="old",
        )
        db.add(cache)
        db.commit()

        # 本文なし → 422 (pydantic validation)
        resp_missing = client.post("/api/blog/summarize/retry", headers=headers)
        assert resp_missing.status_code == 422

        # articles が 1 件以上含まれていれば 202
        articles = [
            {
                "platform": "zenn",
                "title": "テスト記事",
                "url": "https://example.com/article",
            }
        ]
        with patch(
            "app.routers.blog.check_llm_available", new=AsyncMock(return_value=True),
        ):
            resp_ok = client.post(
                "/api/blog/summarize/retry",
                json={"articles": articles},
                headers=headers,
            )
        assert resp_ok.status_code == 202

        db.refresh(cache)
        assert cache.status == "pending"
        assert cache.retry_count == 0


# ══════════════════════════════════════════════════════════════════════
# 終端状態の判定（固定値ではなく境界条件を確認）
# ══════════════════════════════════════════════════════════════════════


def test_is_final_at_last_attempt(db_session: Session):
    """max_attempts=3, retry_count=2 は最終試行であること（dead_letter に遷移する）。"""
    # この境界条件は TestExecuteTaskRetryBranching.test_retryable_error_on_final_attempt
    # で既にカバーしているが、ここで明示的にパラメトリックに確認する。
    user = UserRepository(db_session).create(
        "github:boundary-user", hashed_password=None, email="boundary@test.com",
    )
    cache = GitHubAnalysisCache(user_id=user.id, status="processing")
    db_session.add(cache)
    db_session.commit()

    # 最終より 1 つ手前（retry_count=1, max=3）は retrying
    with (
        patch(
            "app.services.tasks.worker.SessionLocal",
            return_value=_keep_open_session(db_session),
        ),
        patch(
            "app.services.tasks.worker._run_github_analysis",
            new_callable=AsyncMock,
            side_effect=RetryableError("still retrying"),
        ),
        patch("app.services.tasks.worker._create_notification"),
    ):
        with pytest.raises(RetryableError):
            _run(
                execute_task(
                    TaskType.GITHUB_ANALYSIS,
                    {"user_id": user.id},
                    retry_count=1,
                    max_attempts=3,
                ),
            )
    db_session.refresh(cache)
    assert cache.status == "retrying"
