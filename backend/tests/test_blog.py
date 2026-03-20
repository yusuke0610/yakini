from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
from sqlalchemy.orm.session import Session

from conftest import auth_header

# テスト中は外部 API 呼び出しをモックし、常にユーザーが存在する扱いにする
_VERIFY_PATCH = "app.routers.blog.verify_user_exists"


def test_add_blog_account(client: TestClient) -> None:
    """POST でアカウント登録できること。"""
    auth_header(client)
    with patch(_VERIFY_PATCH, new_callable=AsyncMock, return_value=True):
        resp = client.post(
            "/api/blog/accounts",
            json={
                "platform": "zenn",
                "username": "testuser",
            },
        )
    assert resp.status_code == 201
    data = resp.json()
    assert data["platform"] == "zenn"
    assert data["username"] == "testuser"
    assert "id" in data


def test_add_account_user_not_found(client: TestClient) -> None:
    """存在しないユーザー名で登録すると 404。"""
    auth_header(client)
    with patch(_VERIFY_PATCH, new_callable=AsyncMock, return_value=False):
        resp = client.post(
            "/api/blog/accounts",
            json={
                "platform": "zenn",
                "username": "nonexistent_user_xyz",
            },
        )
    assert resp.status_code == 404
    assert "見つかりません" in resp.json()["detail"]


def test_add_duplicate_account(client: TestClient) -> None:
    """同じ platform は重複登録できないこと。"""
    auth_header(client)
    with patch(_VERIFY_PATCH, new_callable=AsyncMock, return_value=True):
        client.post(
            "/api/blog/accounts",
            json={
                "platform": "zenn",
                "username": "testuser",
            },
        )
        resp = client.post(
            "/api/blog/accounts",
            json={
                "platform": "zenn",
                "username": "testuser2",
            },
        )
    assert resp.status_code == 409


def test_list_blog_accounts(client: TestClient) -> None:
    """GET でアカウント一覧取得。"""
    auth_header(client)
    with patch(_VERIFY_PATCH, new_callable=AsyncMock, return_value=True):
        client.post("/api/blog/accounts", json={"platform": "zenn", "username": "u1"})
        client.post("/api/blog/accounts", json={"platform": "note", "username": "u2"})

    resp = client.get("/api/blog/accounts")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2


def test_delete_blog_account(client: TestClient) -> None:
    """DELETE でアカウント解除 + 記事も削除。"""
    auth_header(client)
    with patch(_VERIFY_PATCH, new_callable=AsyncMock, return_value=True):
        resp = client.post(
            "/api/blog/accounts",
            json={
                "platform": "zenn",
                "username": "testuser",
            },
        )
    account_id = resp.json()["id"]

    resp = client.delete(f"/api/blog/accounts/{account_id}")
    assert resp.status_code == 204

    resp = client.get("/api/blog/accounts")
    assert resp.json() == []


def test_list_blog_articles(client: TestClient) -> None:
    """GET で記事一覧取得。"""
    auth_header(client)
    resp = client.get("/api/blog/articles")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_blog_articles_filter_platform(client: TestClient) -> None:
    """platform パラメータでフィルタ。"""
    auth_header(client)
    resp = client.get("/api/blog/articles?platform=zenn")
    assert resp.status_code == 200
    assert resp.json() == []


def test_sync_requires_auth(client: TestClient) -> None:
    """認証なしで sync → 401。"""
    resp = client.post("/api/blog/accounts/dummy-id/sync")
    assert resp.status_code == 401


def test_upsert_articles_no_duplicates(client: TestClient, db_session: Session) -> None:
    """同じ記事を2回 upsert しても重複しない。"""
    auth_header(client)

    # アカウント作成
    with patch(_VERIFY_PATCH, new_callable=AsyncMock, return_value=True):
        resp = client.post(
            "/api/blog/accounts",
            json={
                "platform": "zenn",
                "username": "testuser",
            },
        )
    account_id = resp.json()["id"]

    # ユーザーIDを取得
    from app.repositories import BlogArticleRepository, UserRepository

    user = UserRepository(db_session).get_by_username("testuser")
    repo = BlogArticleRepository(db_session, user.id)

    articles = [
        {
            "account_id": account_id,
            "platform": "zenn",
            "external_id": "slug-1",
            "title": "記事1",
            "url": "https://zenn.dev/testuser/articles/slug-1",
            "published_at": "2026-03-01",
            "likes_count": 10,
            "summary": "",
            "tags": ["Python"],
        },
    ]

    count1 = repo.upsert_many(articles)
    assert count1 == 1

    # 同じ記事を再度 upsert
    count2 = repo.upsert_many(articles)
    assert count2 == 0

    # 合計1件のまま
    assert repo.count_by_user() == 1


def test_list_blog_articles_returns_platform_and_tags(
    client: TestClient, db_session: Session
) -> None:
    auth_header(client)

    with patch(_VERIFY_PATCH, new_callable=AsyncMock, return_value=True):
        resp = client.post(
            "/api/blog/accounts",
            json={
                "platform": "zenn",
                "username": "testuser",
            },
        )
    account_id = resp.json()["id"]

    from app.repositories import BlogArticleRepository, UserRepository

    user = UserRepository(db_session).get_by_username("testuser")
    repo = BlogArticleRepository(db_session, user.id)
    repo.upsert_many(
        [
            {
                "account_id": account_id,
                "platform": "zenn",
                "external_id": "slug-2",
                "title": "記事2",
                "url": "https://zenn.dev/testuser/articles/slug-2",
                "published_at": "2026-03-02",
                "likes_count": 5,
                "summary": "要約",
                "tags": ["Python", "FastAPI"],
            }
        ]
    )

    resp = client.get("/api/blog/articles")
    assert resp.status_code == 200
    data = resp.json()
    assert data[0]["platform"] == "zenn"
    assert data[0]["tags"] == ["Python", "FastAPI"]
