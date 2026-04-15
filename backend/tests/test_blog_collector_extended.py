"""
ブログコレクター（fetch_articles / fetch_zenn_articles / 複数ページ）の拡張テスト。

対象モジュール: app.services.blog.collector
テスト方針:
  - 外部 API は httpx.AsyncClient をモック化してテスト
  - fetch_articles のディスパッチロジックを全プラットフォームで検証
  - 複数ページネーション・空レスポンス等の境界値をカバー
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.services.blog.collector import (
    UnsupportedBlogPlatformError,
    fetch_articles,
    fetch_zenn_articles,
)


def _run(coro):
    """async 関数を同期的に実行するヘルパー。"""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def _make_mock_client(responses: list):
    """連続する GET レスポンスを返すモック AsyncClient を生成する。"""
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    side_effects = []
    for resp_data in responses:
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json = MagicMock(return_value=resp_data)
        side_effects.append(mock_resp)

    mock_client.get = AsyncMock(side_effect=side_effects)
    return mock_client


# ── fetch_zenn_articles ───────────────────────────────────────────────────


class TestFetchZennArticles:
    def test_success_single_page(self):
        """Zenn 記事を正常に 1 ページ取得できること。"""
        api_json = {
            "articles": [
                {
                    "slug": "abc123",
                    "title": "Zenn テスト記事",
                    "published_at": "2026-01-01T12:00:00.000Z",
                    "liked_count": 20,
                    "topics": [{"display_name": "Python"}, {"display_name": "FastAPI"}],
                }
            ],
            "next_page": None,
        }
        mock_client = _make_mock_client([api_json])

        with patch("app.services.blog.collector.httpx.AsyncClient", return_value=mock_client):
            articles = _run(fetch_zenn_articles("testuser"))

        assert len(articles) == 1
        assert articles[0]["platform"] == "zenn"
        assert articles[0]["external_id"] == "abc123"
        assert articles[0]["title"] == "Zenn テスト記事"
        assert articles[0]["url"] == "https://zenn.dev/testuser/articles/abc123"
        assert articles[0]["published_at"] == "2026-01-01"
        assert articles[0]["likes_count"] == 20
        assert "Python" in articles[0]["tags"]
        assert "FastAPI" in articles[0]["tags"]

    def test_empty_articles(self):
        """記事が 0 件の場合、空リストが返ること。"""
        api_json = {"articles": [], "next_page": None}
        mock_client = _make_mock_client([api_json])

        with patch("app.services.blog.collector.httpx.AsyncClient", return_value=mock_client):
            articles = _run(fetch_zenn_articles("emptyuser"))

        assert articles == []

    def test_multi_page_fetched(self):
        """複数ページの場合、すべてのページを取得すること。"""
        page1 = {
            "articles": [
                {
                    "slug": "slug1",
                    "title": "記事1",
                    "published_at": "2026-01-01T00:00:00Z",
                    "liked_count": 5,
                    "topics": [],
                }
            ],
            "next_page": 2,
        }
        page2 = {
            "articles": [
                {
                    "slug": "slug2",
                    "title": "記事2",
                    "published_at": "2026-02-01T00:00:00Z",
                    "liked_count": 10,
                    "topics": [],
                }
            ],
            "next_page": None,
        }
        mock_client = _make_mock_client([page1, page2])

        with patch("app.services.blog.collector.httpx.AsyncClient", return_value=mock_client):
            articles = _run(fetch_zenn_articles("testuser"))

        assert len(articles) == 2
        slugs = {a["external_id"] for a in articles}
        assert "slug1" in slugs
        assert "slug2" in slugs

    def test_no_published_at_becomes_none(self):
        """published_at が None の場合、published_at が None になること。"""
        api_json = {
            "articles": [
                {
                    "slug": "draft",
                    "title": "下書き",
                    "published_at": None,
                    "liked_count": 0,
                    "topics": [],
                }
            ],
            "next_page": None,
        }
        mock_client = _make_mock_client([api_json])

        with patch("app.services.blog.collector.httpx.AsyncClient", return_value=mock_client):
            articles = _run(fetch_zenn_articles("testuser"))

        assert articles[0]["published_at"] is None

    def test_topics_as_list_of_dicts(self):
        """topics が dict リストの場合、display_name が取得されること。"""
        api_json = {
            "articles": [
                {
                    "slug": "s1",
                    "title": "記事",
                    "published_at": "2026-01-01T00:00:00Z",
                    "liked_count": 0,
                    "topics": [
                        {"display_name": "Go"},
                        {"name": "Docker"},  # display_name なしのケース
                    ],
                }
            ],
            "next_page": None,
        }
        mock_client = _make_mock_client([api_json])

        with patch("app.services.blog.collector.httpx.AsyncClient", return_value=mock_client):
            articles = _run(fetch_zenn_articles("testuser"))

        assert "Go" in articles[0]["tags"]
        assert "Docker" in articles[0]["tags"]


# ── fetch_articles ────────────────────────────────────────────────────────


class TestFetchArticles:
    def test_dispatches_to_zenn(self):
        """platform=zenn のとき fetch_zenn_articles が呼ばれること。"""
        with patch(
            "app.services.blog.collector.fetch_zenn_articles",
            new_callable=AsyncMock,
            return_value=[{"platform": "zenn"}],
        ) as mock_fn:
            result = _run(fetch_articles("zenn", "user"))

        mock_fn.assert_called_once_with("user")
        assert result == [{"platform": "zenn"}]

    def test_dispatches_to_note(self):
        """platform=note のとき fetch_note_articles が呼ばれること。"""
        with patch(
            "app.services.blog.collector.fetch_note_articles",
            new_callable=AsyncMock,
            return_value=[{"platform": "note"}],
        ) as mock_fn:
            result = _run(fetch_articles("note", "user"))

        mock_fn.assert_called_once_with("user")
        assert result == [{"platform": "note"}]

    def test_dispatches_to_qiita(self):
        """platform=qiita のとき fetch_qiita_articles が呼ばれること。"""
        with patch(
            "app.services.blog.collector.fetch_qiita_articles",
            new_callable=AsyncMock,
            return_value=[{"platform": "qiita"}],
        ) as mock_fn:
            result = _run(fetch_articles("qiita", "user"))

        mock_fn.assert_called_once_with("user")
        assert result == [{"platform": "qiita"}]

    def test_unsupported_platform_raises(self):
        """未対応プラットフォームで UnsupportedBlogPlatformError が送出されること。"""
        with pytest.raises(UnsupportedBlogPlatformError):
            _run(fetch_articles("hatena", "user"))

    def test_unsupported_platform_raises_with_medium(self):
        """medium のような未対応プラットフォームでも例外が出ること。"""
        with pytest.raises(UnsupportedBlogPlatformError):
            _run(fetch_articles("medium", "user"))


# ── fetch_note_articles (複数ページ) ─────────────────────────────────────


class TestFetchNoteMultiPage:
    def _make_note_content(self, note_id, title):
        return {
            "id": note_id,
            "name": title,
            "noteUrl": f"https://note.com/user/n/n{note_id}",
            "publishAt": "2026-01-01T00:00:00.000+0900",
            "likeCount": 0,
            "body": "本文",
            "hashtags": [],
        }

    def test_multi_page_fetched(self):
        """isLastPage=False の場合に次のページを取得すること。"""
        from app.services.blog.collector import fetch_note_articles

        page1_data = {
            "data": {
                "contents": [self._make_note_content(1, "記事1")],
                "isLastPage": False,
            }
        }
        page2_data = {
            "data": {
                "contents": [self._make_note_content(2, "記事2")],
                "isLastPage": True,
            }
        }
        mock_client = _make_mock_client([page1_data, page2_data])

        with (
            patch("app.services.blog.collector.httpx.AsyncClient", return_value=mock_client),
            patch("asyncio.sleep", new_callable=AsyncMock),
        ):
            articles = _run(fetch_note_articles("user"))

        assert len(articles) == 2

    def test_empty_contents_stops_pagination(self):
        """contents が空リストの場合にページネーションが終了すること。"""
        from app.services.blog.collector import fetch_note_articles

        empty_page = {"data": {"contents": [], "isLastPage": True}}
        mock_client = _make_mock_client([empty_page])

        with patch("app.services.blog.collector.httpx.AsyncClient", return_value=mock_client):
            articles = _run(fetch_note_articles("user"))

        assert articles == []


# ── fetch_qiita_articles (複数ページ) ────────────────────────────────────


class TestFetchQiitaMultiPage:
    def _make_qiita_item(self, item_id, title):
        return {
            "id": item_id,
            "title": title,
            "url": f"https://qiita.com/user/items/{item_id}",
            "created_at": "2026-01-01T10:00:00+09:00",
            "likes_count": 0,
            "tags": [],
        }

    def test_multi_page_fetched(self):
        """per_page 件数が揃った場合に次のページを取得すること。"""
        from app.services.blog.collector import fetch_qiita_articles

        # per_page=100 なので 100 件返すと次ページをフェッチする
        page1 = [self._make_qiita_item(str(i), f"記事{i}") for i in range(100)]
        page2 = [self._make_qiita_item("100", "最終記事")]
        mock_client = _make_mock_client([page1, page2])

        with (
            patch("app.services.blog.collector.httpx.AsyncClient", return_value=mock_client),
            patch("asyncio.sleep", new_callable=AsyncMock),
        ):
            articles = _run(fetch_qiita_articles("user"))

        assert len(articles) == 101

    def test_empty_response_stops(self):
        """空レスポンスでページネーションが終了すること。"""
        from app.services.blog.collector import fetch_qiita_articles

        mock_client = _make_mock_client([[]])

        with patch("app.services.blog.collector.httpx.AsyncClient", return_value=mock_client):
            articles = _run(fetch_qiita_articles("user"))

        assert articles == []

    def test_partial_page_stops(self):
        """per_page 未満の件数で最終ページと判断されること。"""
        from app.services.blog.collector import fetch_qiita_articles

        partial_page = [self._make_qiita_item(str(i), f"記事{i}") for i in range(5)]
        mock_client = _make_mock_client([partial_page])

        with patch("app.services.blog.collector.httpx.AsyncClient", return_value=mock_client):
            articles = _run(fetch_qiita_articles("user"))

        assert len(articles) == 5
