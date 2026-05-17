"""ブログ AI サマリ生成・サマリキャッシュ API の統合テスト。"""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

from app.models import BlogSummaryCache
from app.repositories import UserRepository
from fastapi.testclient import TestClient
from sqlalchemy.orm.session import Session

from conftest import auth_header

_LLM_AVAILABLE_PATCH = "app.routers.blog.summarize.check_llm_available"


def test_summarize_blog_returns_202_when_llm_available(client: TestClient) -> None:
    """LLM 利用可能時は 202 で pending を返す。"""
    headers = auth_header(client)
    with patch(_LLM_AVAILABLE_PATCH, new_callable=AsyncMock, return_value=True):
        resp = client.post("/api/blog/summarize", headers=headers)
    assert resp.status_code == 202
    data = resp.json()
    assert data["status"] == "pending"
    assert data["available"] is False


def test_summarize_blog_returns_unavailable_when_llm_not_available(client: TestClient) -> None:
    """LLM 利用不可なら available=false を返す。"""
    headers = auth_header(client)
    with patch(_LLM_AVAILABLE_PATCH, new_callable=AsyncMock, return_value=False):
        resp = client.post("/api/blog/summarize", headers=headers)
    assert resp.status_code == 202
    assert resp.json()["available"] is False


# ── キャッシュ TTL ─────────────────────────────────────────────────────────


def test_get_summary_cache_returns_unavailable_when_expired(
    client: TestClient, db_session: Session
) -> None:
    """expires_at が過去のキャッシュは無効と見なし available=false を返す。"""
    headers = auth_header(client)
    user = UserRepository(db_session).get_by_username("testuser")
    db_session.add(
        BlogSummaryCache(
            user_id=user.id,
            summary="古い分析結果",
            status="completed",
            expires_at=datetime.now(timezone.utc) - timedelta(days=1),
        )
    )
    db_session.commit()

    resp = client.get("/api/blog/summary-cache", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["available"] is False
    assert data["summary"] == ""

    # レコードが削除されていること
    assert db_session.query(BlogSummaryCache).filter_by(user_id=user.id).first() is None


def test_get_summary_cache_returns_data_when_not_expired(
    client: TestClient, db_session: Session
) -> None:
    """expires_at が未来のキャッシュは有効と見なし summary を返す。"""
    headers = auth_header(client)
    user = UserRepository(db_session).get_by_username("testuser")
    db_session.add(
        BlogSummaryCache(
            user_id=user.id,
            summary="有効な分析結果",
            status="completed",
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
    )
    db_session.commit()

    resp = client.get("/api/blog/summary-cache", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["available"] is True
    assert data["summary"] == "有効な分析結果"


def test_summarize_blog_allows_regenration_when_cache_expired(
    client: TestClient, db_session: Session
) -> None:
    """期限切れキャッシュは pending/processing 扱いにならず再生成を許可する。"""
    headers = auth_header(client)
    user = UserRepository(db_session).get_by_username("testuser")
    db_session.add(
        BlogSummaryCache(
            user_id=user.id,
            summary="古い要約",
            status="completed",
            expires_at=datetime.now(timezone.utc) - timedelta(days=1),
        )
    )
    db_session.commit()

    with patch(_LLM_AVAILABLE_PATCH, new_callable=AsyncMock, return_value=True):
        resp = client.post("/api/blog/summarize", headers=headers)
    assert resp.status_code == 202
    assert resp.json()["status"] == "pending"
