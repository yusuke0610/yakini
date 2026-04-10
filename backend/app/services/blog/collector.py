"""Zenn / note からブログ記事を取得するサービス。"""

import asyncio
import logging

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
    """note API v2 から記事を取得する。全ページ分をフェッチ。"""
    articles: list[dict] = []
    page = 1
    headers = {"User-Agent": "DevForge/1.0"}

    async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
        while True:
            resp = await client.get(
                f"https://note.com/api/v2/creators/{username}/contents",
                params={"kind": "note", "page": page},
            )
            resp.raise_for_status()
            data = resp.json()

            notes = data.get("data", {}).get("contents", [])
            if not notes:
                break

            for item in notes:
                note_url = item.get("noteUrl", "")
                external_id = str(item.get("id", ""))
                published_at = (
                    item.get("publishAt", "")[:10] if item.get("publishAt") else None
                )
                hashtags = item.get("hashtags", [])
                tag_names = [
                    h.get("hashtag", {}).get("name", "")
                    for h in hashtags
                    if isinstance(h, dict)
                ]
                body = item.get("body") or ""

                articles.append(
                    {
                        "platform": "note",
                        "external_id": external_id,
                        "title": item.get("name", ""),
                        "url": note_url,
                        "published_at": published_at,
                        "likes_count": item.get("likeCount", 0),
                        "summary": body[:500],
                        "tags": [t for t in tag_names if t],
                    }
                )

            is_last_page = data.get("data", {}).get("isLastPage", True)
            if is_last_page:
                break
            page += 1
            await asyncio.sleep(0.5)

    return articles


async def verify_user_exists(platform: str, username: str) -> bool:
    """プラットフォーム上にユーザーが存在するか検証する。"""
    try:
        if platform == "zenn":
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"https://zenn.dev/api/users/{username}")
                return resp.status_code == 200
        if platform == "note":
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"https://note.com/api/v2/creators/{username}/contents",
                    params={"kind": "note", "page": 1},
                )
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
