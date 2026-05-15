"""
攻撃者視点のエッジケーステスト。

以下のパターンを 1 ファイルに集約する:
- TestNoAuthAccess: 認証なしでのアクセス
- TestAdminTokenRequired: master-data 書込の admin 認可
- TestInternalSecret: /internal/tasks のなりすまし
- TestIDOR: 他ユーザーリソースの read/update/delete
- TestSQLInjection: path / query / body へのメタ文字注入
- TestBoundaryValues: 空文字・上限超過・負数
- TestPathParamInjection: UUID / int 期待箇所への型違反
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from app.models import (
    BlogAccount,
    BlogSummaryCache,
    CareerAnalysis,
    GitHubAnalysisCache,
    Notification,
    Resume,
    User,
)
from app.repositories import UserRepository
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from conftest import auth_header

# ── 共通定数・ヘルパー ──────────────────────────────────────────


# 攻撃者が試しがちな SQL インジェクションペイロード。
SQLI_PAYLOADS: tuple[str, ...] = (
    "' OR '1'='1",
    "'; DROP TABLE users;--",
    '" OR 1=1 --',
    "' UNION SELECT id FROM users --",
    "admin'/*",
)

# 適当な UUID v4 形式の文字列。実在しない resume_id として使う。
DUMMY_UUID = "00000000-0000-0000-0000-000000000001"


_RESUME_PAYLOAD: dict = {
    "full_name": "山田 太郎",
    "career_summary": "キャリアサマリー",
    "self_pr": "自己PR",
    "experiences": [],
    "qualifications": [],
}


def _create_resume(client: TestClient, headers: dict[str, str]) -> str:
    """resume を作成し、id を返す。"""
    resp = client.post("/api/resumes", json=_RESUME_PAYLOAD, headers=headers)
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def _count(db, model) -> int:
    """テーブルの行数を取得する。"""
    return db.scalar(select(func.count()).select_from(model)) or 0


def _ensure_user(db, username: str) -> User:
    """指定 username のユーザーを取得または作成する。auth_header に依存せず直挿しする用途。"""
    repo = UserRepository(db)
    user = repo.get_by_username(username)
    if not user:
        user = repo.create(username, hashed_password=None, email=f"{username}@example.com")
    return user


# ── 1. 認証なしでのアクセス ─────────────────────────────────────


_PROTECTED_ENDPOINTS: list[tuple[str, str]] = [
    ("post", "/api/resumes"),
    ("get", "/api/resumes/latest"),
    ("get", f"/api/resumes/{DUMMY_UUID}"),
    ("put", f"/api/resumes/{DUMMY_UUID}"),
    ("delete", "/api/resumes"),
    ("get", f"/api/resumes/{DUMMY_UUID}/pdf"),
    ("get", f"/api/resumes/{DUMMY_UUID}/markdown"),
    ("post", "/api/career-analysis/generate"),
    ("get", "/api/career-analysis/"),
    ("get", "/api/career-analysis/1"),
    ("get", "/api/career-analysis/1/status"),
    ("post", "/api/career-analysis/1/retry"),
    ("delete", "/api/career-analysis/1"),
    ("get", "/api/blog/accounts"),
    ("post", "/api/blog/accounts"),
    ("patch", "/api/blog/accounts/zenn"),
    ("delete", "/api/blog/accounts/x"),
    ("get", "/api/blog/articles"),
    ("post", "/api/blog/accounts/x/sync"),
    ("get", "/api/blog/summary-cache"),
    ("get", "/api/blog/summary-cache/status"),
    ("post", "/api/blog/summarize"),
    ("post", "/api/blog/summarize/retry"),
    ("get", "/api/blog/score"),
    ("get", "/api/intelligence/cache"),
    ("get", "/api/intelligence/cache/status"),
    ("get", "/api/intelligence/progress"),
    ("post", "/api/intelligence/analyze"),
    ("post", "/api/intelligence/analyze/retry"),
    ("post", "/api/intelligence/position-advice"),
    ("get", "/api/notifications"),
    ("get", "/api/notifications/unread-count"),
    ("patch", "/api/notifications/abc/read"),
    ("post", "/api/notifications/read-all"),
]


class TestNoAuthAccess:
    """Cookie / CSRF なしで保護対象を叩くと 401/403 が返ることを固定化する。"""

    @pytest.mark.parametrize("method,path", _PROTECTED_ENDPOINTS)
    def test_protected_endpoint_rejects_unauthenticated(
        self, client: TestClient, method: str, path: str
    ) -> None:
        resp = getattr(client, method)(path)
        assert resp.status_code in (401, 403), (
            f"{method.upper()} {path} の status は 401/403 期待だが {resp.status_code}: {resp.text}"
        )

    def test_health_endpoint_is_public(self, client: TestClient) -> None:
        assert client.get("/health").status_code == 200

    def test_master_data_list_is_public(self, client: TestClient) -> None:
        """マスタの GET は公開（フロントが認証前に取得する設計）。"""
        assert client.get("/api/master-data/qualification").status_code == 200
        assert client.get("/api/master-data/technology-stack").status_code == 200


# ── 2. Admin token 必須の検証 ─────────────────────────────────


class TestAdminTokenRequired:
    """master-data の書込系は admin Bearer token を要求する。"""

    @pytest.mark.parametrize(
        "method,path,body",
        [
            ("post", "/api/master-data/qualification", {"name": "x", "sort_order": 0}),
            ("put", "/api/master-data/qualification/anything", {"name": "x", "sort_order": 0}),
            ("delete", "/api/master-data/qualification/anything", None),
            (
                "post",
                "/api/master-data/technology-stack",
                {"category": "c", "name": "x", "sort_order": 0},
            ),
            (
                "put",
                "/api/master-data/technology-stack/anything",
                {"category": "c", "name": "x", "sort_order": 0},
            ),
            ("delete", "/api/master-data/technology-stack/anything", None),
        ],
    )
    def test_missing_authorization_returns_401(
        self, client: TestClient, method: str, path: str, body: dict | None
    ) -> None:
        if body is None:
            resp = getattr(client, method)(path)
        else:
            resp = getattr(client, method)(path, json=body)
        assert resp.status_code == 401

    def test_wrong_bearer_token_returns_403(self, client: TestClient) -> None:
        resp = client.post(
            "/api/master-data/qualification",
            json={"name": "x", "sort_order": 0},
            headers={"Authorization": "Bearer wrong-token"},
        )
        assert resp.status_code == 403


# ── 3. Internal task endpoint ─────────────────────────────────


class TestInternalSecret:
    """Cloud Tasks コールバックには X-CloudTasks-QueueName を要求する。"""

    def test_unknown_task_type_returns_400(self, client: TestClient) -> None:
        resp = client.post("/internal/tasks/totally-unknown-type", json={})
        assert resp.status_code == 400

    def test_missing_cloud_tasks_header_returns_403(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """TASK_RUNNER=cloud_tasks では X-CloudTasks-QueueName が無いと 403。"""
        monkeypatch.setenv("TASK_RUNNER", "cloud_tasks")
        resp = client.post("/internal/tasks/blog_summarize", json={"user_id": "x"})
        assert resp.status_code == 403


# ── 4. IDOR ────────────────────────────────────────────────────


class TestIDOR:
    """user A のリソースは user B からは見えない・操作できないことを固定化する。"""

    def test_resume_get_by_id_returns_404_for_other_user(self, client: TestClient) -> None:
        headers_a = auth_header(client, "idor-resume-a")
        a_id = _create_resume(client, headers_a)
        headers_b = auth_header(client, "idor-resume-b")
        resp = client.get(f"/api/resumes/{a_id}", headers=headers_b)
        assert resp.status_code == 404

    def test_resume_put_does_not_modify_other_user_data(
        self, client: TestClient, db_session
    ) -> None:
        headers_a = auth_header(client, "idor-resume-put-a")
        a_id = _create_resume(client, headers_a)
        headers_b = auth_header(client, "idor-resume-put-b")
        resp = client.put(
            f"/api/resumes/{a_id}",
            json={**_RESUME_PAYLOAD, "full_name": "侵入者"},
            headers=headers_b,
        )
        assert resp.status_code == 404
        # A の full_name が書き換わっていないこと
        user_a = UserRepository(db_session).get_by_username("idor-resume-put-a")
        assert user_a is not None
        a_resume = db_session.scalar(select(Resume).where(Resume.user_id == user_a.id))
        assert a_resume is not None
        assert a_resume.full_name == _RESUME_PAYLOAD["full_name"]

    def test_resume_download_endpoints_reject_other_user(self, client: TestClient) -> None:
        headers_a = auth_header(client, "idor-resume-dl-a")
        a_id = _create_resume(client, headers_a)
        headers_b = auth_header(client, "idor-resume-dl-b")
        for suffix in ("pdf", "markdown"):
            resp = client.get(f"/api/resumes/{a_id}/{suffix}", headers=headers_b)
            assert resp.status_code == 404, f"{suffix} should reject other-user access"

    def test_resume_delete_does_not_touch_other_user_data(
        self, client: TestClient, db_session
    ) -> None:
        """B が DELETE しても A の resume は残り、B 自身は 404。"""
        headers_a = auth_header(client, "idor-resume-del-a")
        _create_resume(client, headers_a)
        headers_b = auth_header(client, "idor-resume-del-b")
        resp = client.delete("/api/resumes", headers=headers_b)
        assert resp.status_code == 404
        user_a = UserRepository(db_session).get_by_username("idor-resume-del-a")
        assert user_a is not None
        remaining = db_session.scalar(select(Resume).where(Resume.user_id == user_a.id))
        assert remaining is not None

    def test_career_analysis_status_returns_404_for_other_user(
        self, client: TestClient, db_session
    ) -> None:
        user_a = _ensure_user(db_session, "idor-career-status-a")
        analysis = self._insert_career_analysis(db_session, user_a.id)
        headers_b = auth_header(client, "idor-career-status-b")
        resp = client.get(f"/api/career-analysis/{analysis.id}/status", headers=headers_b)
        assert resp.status_code == 404

    def test_career_analysis_delete_does_not_touch_other_user_data(
        self, client: TestClient, db_session
    ) -> None:
        user_a = _ensure_user(db_session, "idor-career-del-a")
        analysis = self._insert_career_analysis(db_session, user_a.id)
        analysis_id = analysis.id
        headers_b = auth_header(client, "idor-career-del-b")
        resp = client.delete(f"/api/career-analysis/{analysis_id}", headers=headers_b)
        assert resp.status_code == 404
        remaining = db_session.scalar(
            select(CareerAnalysis).where(CareerAnalysis.id == analysis_id)
        )
        assert remaining is not None

    def test_career_analysis_retry_returns_404_for_other_user(
        self, client: TestClient, db_session
    ) -> None:
        user_a = _ensure_user(db_session, "idor-career-retry-a")
        analysis = self._insert_career_analysis(db_session, user_a.id, status="dead_letter")
        headers_b = auth_header(client, "idor-career-retry-b")
        resp = client.post(f"/api/career-analysis/{analysis.id}/retry", headers=headers_b)
        assert resp.status_code == 404

    def test_blog_account_delete_does_not_touch_other_user_data(
        self, client: TestClient, db_session
    ) -> None:
        user_a = _ensure_user(db_session, "idor-blog-del-a")
        account = BlogAccount(user_id=user_a.id, platform="zenn", username="user-a")
        db_session.add(account)
        db_session.commit()
        account_id = account.id
        headers_b = auth_header(client, "idor-blog-del-b")
        resp = client.delete(f"/api/blog/accounts/{account_id}", headers=headers_b)
        assert resp.status_code == 404
        remaining = db_session.scalar(select(BlogAccount).where(BlogAccount.id == account_id))
        assert remaining is not None

    def test_blog_account_patch_does_not_touch_other_user_data(
        self, client: TestClient, db_session
    ) -> None:
        user_a = _ensure_user(db_session, "idor-blog-patch-a")
        account = BlogAccount(user_id=user_a.id, platform="qiita", username="user-a")
        db_session.add(account)
        db_session.commit()
        headers_b = auth_header(client, "idor-blog-patch-b")
        # 早期 404 のため verify_user_exists には到達しないが、念のためモック
        with patch(
            "app.routers.blog.verify_user_exists", new_callable=AsyncMock, return_value=True
        ):
            resp = client.patch(
                "/api/blog/accounts/qiita",
                json={"username": "intruder"},
                headers=headers_b,
            )
        assert resp.status_code == 404
        unchanged = db_session.scalar(
            select(BlogAccount).where(
                BlogAccount.user_id == user_a.id, BlogAccount.platform == "qiita"
            )
        )
        assert unchanged.username == "user-a"

    def test_blog_account_sync_returns_404_for_other_user(
        self, client: TestClient, db_session
    ) -> None:
        user_a = _ensure_user(db_session, "idor-blog-sync-a")
        account = BlogAccount(user_id=user_a.id, platform="zenn", username="user-a")
        db_session.add(account)
        db_session.commit()
        account_id = account.id
        headers_b = auth_header(client, "idor-blog-sync-b")
        resp = client.post(f"/api/blog/accounts/{account_id}/sync", headers=headers_b)
        assert resp.status_code == 404

    def test_blog_summary_cache_does_not_leak_to_other_user(
        self, client: TestClient, db_session
    ) -> None:
        user_a = _ensure_user(db_session, "idor-blog-cache-a")
        cache_a = BlogSummaryCache(
            user_id=user_a.id, summary="A の機密サマリ", status="completed"
        )
        db_session.add(cache_a)
        db_session.commit()
        headers_b = auth_header(client, "idor-blog-cache-b")
        resp = client.get("/api/blog/summary-cache", headers=headers_b)
        assert resp.status_code == 200
        body = resp.json()
        assert body["available"] is False
        assert "A の機密サマリ" not in (body.get("summary") or "")

    def test_intelligence_cache_does_not_leak_to_other_user(
        self, client: TestClient, db_session
    ) -> None:
        user_a = _ensure_user(db_session, "idor-intel-cache-a")
        cache_a = GitHubAnalysisCache(
            user_id=user_a.id,
            analysis_result={"secret": "A だけが見るべきデータ"},
            status="completed",
        )
        db_session.add(cache_a)
        db_session.commit()
        headers_b = auth_header(client, "idor-intel-cache-b")
        resp = client.get("/api/intelligence/cache", headers=headers_b)
        assert resp.status_code == 200
        body = resp.json()
        assert body.get("analysis_result") is None

    def test_notification_mark_read_does_not_touch_other_user(
        self, client: TestClient, db_session
    ) -> None:
        user_a = _ensure_user(db_session, "idor-notif-a")
        notification = Notification(
            user_id=user_a.id,
            task_type="github_analysis",
            status="completed",
            title="A 宛通知",
            is_read=False,
        )
        db_session.add(notification)
        db_session.commit()
        notif_id = notification.id
        headers_b = auth_header(client, "idor-notif-b")
        resp = client.patch(f"/api/notifications/{notif_id}/read", headers=headers_b)
        assert resp.status_code == 404
        unchanged = db_session.scalar(select(Notification).where(Notification.id == notif_id))
        assert unchanged.is_read is False

    @staticmethod
    def _insert_career_analysis(
        db, user_id: str, *, status: str = "pending"
    ) -> CareerAnalysis:
        analysis = CareerAnalysis(
            user_id=user_id,
            version=1,
            target_position="Backend",
            status=status,
        )
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        return analysis


# ── 5. SQL インジェクション ────────────────────────────────────


class TestSQLInjection:
    """SQLi メタ文字を流しても 500 にならず・他レコードを壊さず・他ユーザーデータを返さない。"""

    @pytest.mark.parametrize("payload", SQLI_PAYLOADS)
    def test_resume_full_name_treats_payload_as_literal(
        self, client: TestClient, db_session, payload: str
    ) -> None:
        headers = auth_header(client, "sqli-resume")
        resp = client.post(
            "/api/resumes",
            json={**_RESUME_PAYLOAD, "full_name": payload},
            headers=headers,
        )
        assert resp.status_code == 201
        latest = client.get("/api/resumes/latest", headers=headers)
        assert latest.status_code == 200
        # ペイロードがリテラルとしてそのまま読み出せること
        assert latest.json()["full_name"] == payload
        # users テーブルが破壊されていないこと（少なくとも 1 行は残る）
        assert _count(db_session, User) >= 1

    @pytest.mark.parametrize("payload", SQLI_PAYLOADS)
    def test_resume_path_param_rejects_sqli(
        self, client: TestClient, payload: str
    ) -> None:
        """resume_id は UUID 型なので SQLi 文字列は DB に到達しない。
        UUID 型違反は 422、URL に ``/`` を含むペイロードはルートが一致せず 404 になるが、
        いずれも「攻撃文字列が DB クエリに乗らない」ことを示すので両方を許容する。
        """
        headers = auth_header(client, "sqli-resume-path")
        resp = client.get(f"/api/resumes/{payload}", headers=headers)
        assert resp.status_code in (404, 422), resp.text

    @pytest.mark.parametrize("payload", SQLI_PAYLOADS)
    def test_career_analysis_path_param_rejects_sqli(
        self, client: TestClient, payload: str
    ) -> None:
        """analysis_id は int 型。SQLi 文字列は 422、``/`` を含むペイロードは 404。"""
        headers = auth_header(client, "sqli-career-path")
        resp = client.get(f"/api/career-analysis/{payload}", headers=headers)
        assert resp.status_code in (404, 422), resp.text

    @pytest.mark.parametrize("payload", SQLI_PAYLOADS)
    def test_blog_account_path_returns_404_for_sqli(
        self, client: TestClient, db_session, payload: str
    ) -> None:
        """blog account_id は str 型。SQLAlchemy がパラメタライズして 404。"""
        headers = auth_header(client, "sqli-blog-account")
        resp = client.delete(f"/api/blog/accounts/{payload}", headers=headers)
        assert resp.status_code != 500, resp.text
        assert resp.status_code in (404, 422)
        # users テーブルが破壊されていないこと
        assert _count(db_session, User) >= 1

    @pytest.mark.parametrize("payload", SQLI_PAYLOADS)
    def test_blog_articles_query_filter_handles_sqli(
        self, client: TestClient, payload: str
    ) -> None:
        """?platform= に SQLi を渡しても 200 + 空配列。"""
        headers = auth_header(client, "sqli-blog-articles")
        resp = client.get("/api/blog/articles", params={"platform": payload}, headers=headers)
        assert resp.status_code == 200
        assert resp.json() == []

    @pytest.mark.parametrize("payload", SQLI_PAYLOADS)
    def test_notification_path_returns_404_for_sqli(
        self, client: TestClient, payload: str
    ) -> None:
        headers = auth_header(client, "sqli-notif")
        resp = client.patch(f"/api/notifications/{payload}/read", headers=headers)
        assert resp.status_code != 500, resp.text
        assert resp.status_code in (404, 422)

    @pytest.mark.parametrize("payload", SQLI_PAYLOADS)
    def test_master_data_name_treats_payload_as_literal(
        self, client: TestClient, payload: str
    ) -> None:
        """admin token 経由で SQLi を保存しても、文字列リテラル扱いで他テーブルが壊れない。"""
        resp = client.post(
            "/api/master-data/qualification",
            json={"name": payload, "sort_order": 0},
            headers={"Authorization": "Bearer test-admin-token"},
        )
        assert resp.status_code == 201
        assert resp.json()["name"] == payload
        # 一覧 API が落ちずに 1 件返ること（DROP TABLE が解釈されていない証拠）
        listed = client.get("/api/master-data/qualification")
        assert listed.status_code == 200
        names = [item["name"] for item in listed.json()]
        assert payload in names


# ── 6. 境界値 ─────────────────────────────────────────────────


class TestBoundaryValues:
    """空文字・上限超過・負数などで 422 を返すことを固定化する。"""

    def test_resume_full_name_empty_returns_422(self, client: TestClient) -> None:
        headers = auth_header(client, "bound-resume-empty")
        resp = client.post(
            "/api/resumes",
            json={**_RESUME_PAYLOAD, "full_name": ""},
            headers=headers,
        )
        assert resp.status_code == 422

    def test_resume_full_name_over_max_length_returns_422(self, client: TestClient) -> None:
        headers = auth_header(client, "bound-resume-max")
        resp = client.post(
            "/api/resumes",
            json={**_RESUME_PAYLOAD, "full_name": "あ" * 121},
            headers=headers,
        )
        assert resp.status_code == 422

    def test_resume_career_summary_over_max_length_returns_422(
        self, client: TestClient
    ) -> None:
        headers = auth_header(client, "bound-resume-cs")
        resp = client.post(
            "/api/resumes",
            json={**_RESUME_PAYLOAD, "career_summary": "x" * 2001},
            headers=headers,
        )
        assert resp.status_code == 422

    def test_resume_team_member_count_negative_returns_422(self, client: TestClient) -> None:
        """team.members[].count は ge=0 制約。負数は 422。"""
        headers = auth_header(client, "bound-resume-team-neg")
        payload = {
            **_RESUME_PAYLOAD,
            "experiences": [
                {
                    "company": "X",
                    "business_description": "Y",
                    "start_date": "2024-01",
                    "end_date": "2024-12",
                    "is_current": False,
                    "clients": [
                        {
                            "name": "",
                            "projects": [
                                {
                                    "name": "p",
                                    "team": {
                                        "total": "5",
                                        "members": [{"role": "SE", "count": -1}],
                                    },
                                }
                            ],
                        }
                    ],
                }
            ],
        }
        resp = client.post("/api/resumes", json=payload, headers=headers)
        assert resp.status_code == 422

    def test_career_analysis_target_position_over_max_length_returns_422(
        self, client: TestClient
    ) -> None:
        headers = auth_header(client, "bound-career-max")
        resp = client.post(
            "/api/career-analysis/generate",
            json={"target_position": "x" * 201},
            headers=headers,
        )
        assert resp.status_code == 422

    def test_blog_account_username_empty_returns_422(self, client: TestClient) -> None:
        headers = auth_header(client, "bound-blog-empty")
        resp = client.post(
            "/api/blog/accounts",
            json={"platform": "zenn", "username": ""},
            headers=headers,
        )
        assert resp.status_code == 422

    def test_blog_account_username_over_max_length_returns_422(
        self, client: TestClient
    ) -> None:
        headers = auth_header(client, "bound-blog-max")
        resp = client.post(
            "/api/blog/accounts",
            json={"platform": "zenn", "username": "x" * 121},
            headers=headers,
        )
        assert resp.status_code == 422

    def test_blog_account_unsupported_platform_returns_422(self, client: TestClient) -> None:
        """Literal["zenn", "note", "qiita"] 以外は Pydantic Literal で 422。"""
        headers = auth_header(client, "bound-blog-platform")
        resp = client.post(
            "/api/blog/accounts",
            json={"platform": "unknown", "username": "x"},
            headers=headers,
        )
        assert resp.status_code == 422

    def test_master_data_name_empty_returns_422(self, client: TestClient) -> None:
        resp = client.post(
            "/api/master-data/qualification",
            json={"name": "", "sort_order": 0},
            headers={"Authorization": "Bearer test-admin-token"},
        )
        assert resp.status_code == 422

    def test_master_data_name_over_max_length_returns_422(self, client: TestClient) -> None:
        resp = client.post(
            "/api/master-data/qualification",
            json={"name": "x" * 201, "sort_order": 0},
            headers={"Authorization": "Bearer test-admin-token"},
        )
        assert resp.status_code == 422


# ── 7. パスパラメータ型違反 ────────────────────────────────


class TestPathParamInjection:
    """UUID / int 期待箇所への型違反で 422、整数だが範囲外なら 404 を固定化する。"""

    def test_resume_invalid_uuid_returns_422(self, client: TestClient) -> None:
        headers = auth_header(client, "path-resume")
        resp = client.get("/api/resumes/not-a-uuid", headers=headers)
        assert resp.status_code == 422

    def test_resume_uuid_invalid_format_returns_422(self, client: TestClient) -> None:
        """UUID 形式に合わない文字列は 422 で弾かれ、DB に到達しない。"""
        headers = auth_header(client, "path-resume-bad")
        resp = client.get("/api/resumes/etc-passwd", headers=headers)
        assert resp.status_code == 422

    def test_career_analysis_alpha_id_returns_422(self, client: TestClient) -> None:
        headers = auth_header(client, "path-career-alpha")
        resp = client.get("/api/career-analysis/abc", headers=headers)
        assert resp.status_code == 422

    def test_career_analysis_float_id_returns_422(self, client: TestClient) -> None:
        headers = auth_header(client, "path-career-float")
        resp = client.delete("/api/career-analysis/1.5", headers=headers)
        assert resp.status_code == 422

    def test_career_analysis_negative_id_returns_404(self, client: TestClient) -> None:
        """負数 ID は int としてパースされるが DB ヒットしないため 404。"""
        headers = auth_header(client, "path-career-neg")
        resp = client.get("/api/career-analysis/-1", headers=headers)
        assert resp.status_code == 404
