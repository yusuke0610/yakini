"""ブログスコアリング API (/api/blog/score) の境界値テスト。

scorer 本体のロジックは tests/test_blog_scorer.py で個別に検証する。
ここでは router → scorer の結線が API 経由でも動くことと、
記事 0 件の境界値が破綻しないことを固定化する。
"""

from app.models import BlogAccount
from app.repositories import BlogArticleRepository, UserRepository
from fastapi.testclient import TestClient
from sqlalchemy.orm.session import Session

from conftest import auth_header


def test_get_blog_score_with_no_articles_returns_zero_counts(
    client: TestClient, db_session: Session
) -> None:
    """記事 0 件のユーザーで /api/blog/score が 200 を返し、各種統計が 0 になること。"""
    headers = auth_header(client, "score-empty-user")

    resp = client.get("/api/blog/score", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["tech_article_count"] == 0
    assert data["total_article_count"] == 0
    assert data["avg_monthly_posts"] == 0.0
    assert data["avg_likes"] == 0.0


def test_get_blog_score_aggregates_tech_articles(
    client: TestClient, db_session: Session
) -> None:
    """技術記事 1 件・非技術記事 1 件を保存し、tech_article_count と total_article_count が
    それぞれ正しく分かれて返ること。"""
    headers = auth_header(client, "score-mix-user")

    user = UserRepository(db_session).get_by_username("score-mix-user")
    assert user is not None

    account = BlogAccount(user_id=user.id, platform="zenn", username="score-mix-user")
    db_session.add(account)
    db_session.commit()
    db_session.refresh(account)

    repo = BlogArticleRepository(db_session, user.id)
    repo.upsert_many(
        [
            {
                "account_id": account.id,
                "platform": "zenn",
                "external_id": "tech-1",
                "title": "Python の話",
                "url": "https://example.com/tech-1",
                "published_at": "2026-03-01",
                "likes_count": 10,
                "summary": "",
                "tags": ["Python"],
            },
            {
                "account_id": account.id,
                "platform": "zenn",
                "external_id": "diary-1",
                "title": "旅行日記",
                "url": "https://example.com/diary-1",
                "published_at": "2026-03-02",
                "likes_count": 5,
                "summary": "",
                "tags": ["旅行"],
            },
        ]
    )

    resp = client.get("/api/blog/score", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_article_count"] == 2
    assert data["tech_article_count"] == 1
