from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from conftest import auth_header


def _create_resume(client: TestClient, headers: dict[str, str]) -> None:
    resp = client.post(
        "/api/resumes",
        json={
            "career_summary": "バックエンド中心の開発経験",
            "self_pr": "API 設計が得意",
            "experiences": [],
        },
        headers=headers,
    )
    assert resp.status_code == 201


def test_generate_returns_specific_error_when_llm_is_unavailable(client: TestClient) -> None:
    headers = auth_header(client, "career-llm-off")
    _create_resume(client, headers)

    with patch(
        "app.routers.career_analysis._llm_client.check_available",
        new=AsyncMock(return_value=False),
    ):
        resp = client.post(
            "/api/career-analysis/generate",
            json={"target_position": "Backend Engineer"},
            headers=headers,
        )

    assert resp.status_code == 503
    body = resp.json()
    assert body["code"] == "LLM_UNAVAILABLE"
    assert (
        body["message"]
        == "AI キャリアパス分析サービスが利用できません。LLM の設定または接続状態を確認してください。"
    )
    assert body["error_id"]


def test_generate_returns_202_when_llm_is_available(client: TestClient) -> None:
    """LLM が利用可能なら 202 で pending レコードを返す。"""
    headers = auth_header(client, "career-llm-empty")
    _create_resume(client, headers)

    with patch(
        "app.routers.career_analysis._llm_client.check_available",
        new=AsyncMock(return_value=True),
    ):
        resp = client.post(
            "/api/career-analysis/generate",
            json={"target_position": "Backend Engineer"},
            headers=headers,
        )

    assert resp.status_code == 202
    data = resp.json()
    assert data["status"] == "pending"
    assert data["result"] is None


# ── ユーザー境界テスト ────────────────────────────────────────────────────


def test_user_a_career_analysis_not_accessible_by_user_b(client: TestClient) -> None:
    """user A の CareerAnalysis を user B で取得すると 404 になること。"""
    # user A でレコードを作成
    headers_a = auth_header(client, "boundary-user-a")
    _create_resume(client, headers_a)

    with patch(
        "app.routers.career_analysis._llm_client.check_available",
        new=AsyncMock(return_value=True),
    ):
        resp_a = client.post(
            "/api/career-analysis/generate",
            json={"target_position": "Backend Engineer"},
            headers=headers_a,
        )
    assert resp_a.status_code == 202
    analysis_id = resp_a.json()["id"]

    # user B で user A のレコードにアクセス → 404 になること
    headers_b = auth_header(client, "boundary-user-b")
    resp_b = client.get(f"/api/career-analysis/{analysis_id}", headers=headers_b)
    assert resp_b.status_code == 404


def test_user_a_blog_article_not_accessible_by_user_b(client: TestClient) -> None:
    """user A の BlogArticle を user B で取得しても空リストになること。"""
    from unittest.mock import AsyncMock, patch

    from app.repositories import BlogArticleRepository, UserRepository

    # user A でブログアカウントと記事を作成
    headers_a = auth_header(client, "blog-boundary-a")
    with patch("app.routers.blog.verify_user_exists", new_callable=AsyncMock, return_value=True):
        resp = client.post(
            "/api/blog/accounts",
            json={"platform": "zenn", "username": "boundary-a"},
            headers=headers_a,
        )
    assert resp.status_code == 201
    account_id = resp.json()["id"]

    db = client._db_session
    user_a = UserRepository(db).get_by_username("blog-boundary-a")
    repo_a = BlogArticleRepository(db, user_a.id)
    repo_a.upsert_many([
        {
            "account_id": account_id,
            "platform": "zenn",
            "external_id": "boundary-slug",
            "title": "境界テスト記事",
            "url": "https://zenn.dev/boundary-a/articles/boundary-slug",
            "published_at": "2026-01-01",
            "likes_count": 1,
            "summary": "",
            "tags": [],
        }
    ])

    # user B で記事一覧を取得 → user A の記事は見えないこと
    headers_b = auth_header(client, "blog-boundary-b")
    resp_b = client.get("/api/blog/articles", headers=headers_b)
    assert resp_b.status_code == 200
    assert resp_b.json() == []
