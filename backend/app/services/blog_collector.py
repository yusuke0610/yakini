"""Zenn / note からブログ記事を取得するサービス。"""

import logging
import xml.etree.ElementTree as ET

import httpx

logger = logging.getLogger(__name__)


class UnsupportedBlogPlatformError(ValueError):
    """未対応プラットフォームが指定された場合の例外。"""


class BlogPlatformRequestError(RuntimeError):
    """外部プラットフォームへの接続失敗を表す例外。"""


async def fetch_zenn_articles(username: str) -> list[dict]:
    """Zenn API から記事を取得する。全ページ分をフェッチ。"""
    articles: list[dict] = []
    page = 1

    async with httpx.AsyncClient(timeout=30.0) as client:
        while True:
            resp = await client.get(
                "https://zenn.dev/api/articles",
                params={"username": username, "order": "latest", "page": page},
            )
            resp.raise_for_status()
            data = resp.json()

            for item in data.get("articles", []):
                slug = item.get("slug", "")
                # トピック名を抽出（Zenn API の topics フィールド）
                topics = item.get("topics", [])
                tag_names = [
                    t.get("display_name") or t.get("name", "")
                    for t in topics
                    if isinstance(t, dict)
                ]
                articles.append(
                    {
                        "platform": "zenn",
                        "external_id": slug,
                        "title": item.get("title", ""),
                        "url": f"https://zenn.dev/{username}/articles/{slug}",
                        "published_at": (
                            item.get("published_at", "")[:10] if item.get("published_at") else None
                        ),
                        "likes_count": item.get("liked_count", 0),
                        "summary": "",
                        "tags": tag_names,
                    }
                )

            next_page = data.get("next_page")
            if not next_page:
                break
            page = next_page

    return articles


async def fetch_note_articles(username: str) -> list[dict]:
    """note の RSS フィードから記事を取得する。"""
    articles: list[dict] = []

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(f"https://note.com/{username}/rss")
        resp.raise_for_status()

    root = ET.fromstring(resp.text)
    channel = root.find("channel")
    if channel is None:
        return articles

    for item in channel.findall("item"):
        title = item.findtext("title", "")
        link = item.findtext("link", "")
        pub_date = item.findtext("pubDate", "")
        description = item.findtext("description", "")

        # pubDate を YYYY-MM-DD 形式に変換（例: "Sat, 01 Mar 2026 00:00:00 +0900"）
        published_at = _parse_rss_date(pub_date)

        # URLからexternal_idを抽出
        external_id = link.rstrip("/").split("/")[-1] if link else ""

        # RSS の category 要素からタグを抽出
        tags = [cat.text for cat in item.findall("category") if cat.text]

        articles.append(
            {
                "platform": "note",
                "external_id": external_id,
                "title": title,
                "url": link,
                "published_at": published_at,
                "likes_count": 0,
                "summary": _strip_html(description)[:500] if description else "",
                "tags": tags,
            }
        )

    return articles


def _parse_rss_date(date_str: str) -> str | None:
    """RSS の日付文字列を YYYY-MM-DD 形式に変換する。"""
    if not date_str:
        return None
    try:
        from email.utils import parsedate_to_datetime

        dt = parsedate_to_datetime(date_str)
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return date_str[:10] if len(date_str) >= 10 else None


def _strip_html(text: str) -> str:
    """HTMLタグを除去する。"""
    import re

    return re.sub(r"<[^>]+>", "", text).strip()


async def verify_user_exists(platform: str, username: str) -> bool:
    """プラットフォーム上にユーザーが存在するか検証する。"""
    try:
        if platform == "zenn":
            async with httpx.AsyncClient(timeout=10.0) as client:
                # ユーザー API で存在チェック
                resp = await client.get(
                    f"https://zenn.dev/api/users/{username}",
                )
                return resp.status_code == 200
        elif platform == "note":
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"https://note.com/{username}/rss")
                return resp.status_code == 200
        raise UnsupportedBlogPlatformError(platform)
    except (httpx.ConnectError, httpx.TimeoutException):
        logger.warning("プラットフォーム %s への接続に失敗しました", platform)
        raise BlogPlatformRequestError(platform) from None


async def fetch_articles(platform: str, username: str) -> list[dict]:
    """プラットフォームに応じて適切なフェッチャーを呼ぶ。"""
    if platform == "zenn":
        return await fetch_zenn_articles(username)
    if platform == "note":
        return await fetch_note_articles(username)
    raise UnsupportedBlogPlatformError(platform)
