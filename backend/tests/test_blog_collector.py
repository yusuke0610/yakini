"""ブログコレクター（fetch_note_articles / fetch_zenn_articles / verify_user_exists）のユニットテスト。"""

import asyncio
import xml.etree.ElementTree as ET
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from app.services.blog.collector import (
    BlogPlatformRequestError,
    UnsupportedBlogPlatformError,
    fetch_note_articles,
    fetch_zenn_articles,
    verify_user_exists,
)


def _run(coro):
    """async 関数を同期的に実行するヘルパー。"""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# ── fetch_note_articles テスト ───────────────────────────────────────────


def _build_rss(items: list[dict]) -> str:
    """RSS フィード XML 文字列を構築するヘルパー。"""
    channel = ET.Element("channel")
    for item_data in items:
        item = ET.SubElement(channel, "item")
        for tag, text in item_data.items():
            if tag == "categories":
                for cat_text in text:
                    cat = ET.SubElement(item, "category")
                    cat.text = cat_text
            else:
                el = ET.SubElement(item, tag)
                el.text = text
    root = ET.Element("rss")
    root.append(channel)
    return ET.tostring(root, encoding="unicode")


def test_fetch_note_articles_no_category_returns_empty_tags() -> None:
    """RSS の category なし → tags が空リストになること。"""
    rss_xml = _build_rss(
        [
            {
                "title": "テスト記事",
                "link": "https://note.com/user/n/abc123",
                "pubDate": "Thu, 01 Jan 2026 00:00:00 +0000",
                "description": "<p>本文</p>",
                # category なし
            }
        ]
    )

    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.text = rss_xml

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_resp)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("app.services.blog.collector.httpx.AsyncClient", return_value=mock_client):
        articles = _run(fetch_note_articles("user"))

    assert len(articles) == 1
    assert articles[0]["tags"] == []


def test_fetch_note_articles_with_categories() -> None:
    """RSS の category あり → tags に反映されること。"""
    rss_xml = _build_rss(
        [
            {
                "title": "Python記事",
                "link": "https://note.com/user/n/abc456",
                "pubDate": "Thu, 01 Jan 2026 00:00:00 +0000",
                "description": "概要",
                "categories": ["Python", "FastAPI"],
            }
        ]
    )

    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.text = rss_xml

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_resp)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("app.services.blog.collector.httpx.AsyncClient", return_value=mock_client):
        articles = _run(fetch_note_articles("user"))

    assert articles[0]["tags"] == ["Python", "FastAPI"]


# ── fetch_zenn_articles テスト ───────────────────────────────────────────


def test_fetch_zenn_articles_timeout_raises() -> None:
    """httpx.TimeoutException 発生時は例外が伝播すること。"""
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("timeout"))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("app.services.blog.collector.httpx.AsyncClient", return_value=mock_client):
        with pytest.raises(httpx.TimeoutException):
            _run(fetch_zenn_articles("user"))


# ── verify_user_exists テスト ────────────────────────────────────────────


def test_verify_user_exists_unsupported_platform_raises_error() -> None:
    """未対応プラットフォームでは UnsupportedBlogPlatformError が送出されること。"""
    with pytest.raises(UnsupportedBlogPlatformError):
        _run(verify_user_exists("qiita", "someuser"))


def test_verify_user_exists_zenn_user_found() -> None:
    """Zenn ユーザーが存在する場合は True を返すこと。"""
    mock_resp = MagicMock()
    mock_resp.status_code = 200

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_resp)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("app.services.blog.collector.httpx.AsyncClient", return_value=mock_client):
        result = _run(verify_user_exists("zenn", "testuser"))

    assert result is True


def test_verify_user_exists_zenn_user_not_found() -> None:
    """Zenn ユーザーが存在しない場合は False を返すこと。"""
    mock_resp = MagicMock()
    mock_resp.status_code = 404

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_resp)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("app.services.blog.collector.httpx.AsyncClient", return_value=mock_client):
        result = _run(verify_user_exists("zenn", "nonexistent"))

    assert result is False


def test_verify_user_exists_timeout_raises_blog_platform_request_error() -> None:
    """接続タイムアウト時は BlogPlatformRequestError が送出されること。"""
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("timeout"))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("app.services.blog.collector.httpx.AsyncClient", return_value=mock_client):
        with pytest.raises(BlogPlatformRequestError):
            _run(verify_user_exists("zenn", "user"))
