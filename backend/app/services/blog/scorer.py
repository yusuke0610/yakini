"""
ブログ記事の統計サマリ算出。

技術系記事を判定し、投稿頻度・平均いいね数・投稿数の統計を算出する。
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

logger = logging.getLogger(__name__)

_KEYWORDS_PATH = Path(__file__).with_name("tech_keywords.json")

with _KEYWORDS_PATH.open(encoding="utf-8") as keywords_file:
    _TECH_KEYWORDS: list[str] = json.load(keywords_file)["keywords"]

_TECH_KEYWORDS_LOWER = [keyword.lower() for keyword in _TECH_KEYWORDS]


@dataclass
class ArticleWithTechFlag:
    """技術記事判定結果付きの記事情報。"""

    id: str
    title: str
    url: str
    published_at: str | None
    likes_count: int
    tags: list[str]
    is_tech: bool


@dataclass
class BlogScore:
    """ブログ統計サマリ。"""

    tech_article_count: int = 0
    total_article_count: int = 0
    avg_monthly_posts: float = 0.0
    avg_likes: float = 0.0
    articles: list[ArticleWithTechFlag] = field(default_factory=list)


def is_tech_article(tags: list[str], title: str = "") -> bool:
    """タグまたはタイトルに技術系キーワードが含まれるか判定する。"""
    targets = [tag.lower() for tag in tags] + [title.lower()]
    for target in targets:
        if not target:
            continue
        for keyword in _TECH_KEYWORDS_LOWER:
            if keyword in target:
                return True
    return False



def blog_articles_to_score_dicts(articles: list) -> list[dict]:
    """BlogArticle モデルリストを calculate_blog_score が受け取る dict リストに変換する。

    router が BlogArticle モデルを直接渡せるようにし、フィールド名の二重管理を防ぐ。
    BlogArticle は `published_at`・`tags` プロパティを持つため直接参照できる。
    """
    return [
        {
            "id": str(art.id),
            "title": art.title,
            "url": art.url,
            "published_at": art.published_at,
            "likes_count": art.likes_count,
            "tags": art.tags,
        }
        for art in articles
    ]


def calculate_blog_score(articles: list[dict]) -> BlogScore:
    """ブログ記事一覧から統計サマリを算出する。"""
    scored_articles: list[ArticleWithTechFlag] = []
    tech_articles: list[dict] = []

    for article in articles:
        tags = article.get("tags", [])
        title = article.get("title", "")
        tech = is_tech_article(tags, title)
        scored_articles.append(
            ArticleWithTechFlag(
                id=article.get("id", ""),
                title=article.get("title", ""),
                url=article.get("url", ""),
                published_at=article.get("published_at"),
                likes_count=article.get("likes_count", 0),
                tags=tags,
                is_tech=tech,
            )
        )
        if tech:
            tech_articles.append(article)

    total = len(articles)
    tech_count = len(tech_articles)

    if tech_count == 0:
        return BlogScore(
            tech_article_count=0,
            total_article_count=total,
            articles=scored_articles,
        )

    total_likes = sum(article.get("likes_count", 0) for article in tech_articles)
    avg_likes = total_likes / tech_count

    dates = []
    for article in tech_articles:
        published_at = article.get("published_at")
        if published_at:
            try:
                dates.append(date.fromisoformat(published_at))
            except (TypeError, ValueError):
                pass

    if dates:
        earliest = min(dates)
        today = date.today()
        months = max((today.year - earliest.year) * 12 + (today.month - earliest.month), 1)
        avg_monthly = tech_count / months
    else:
        avg_monthly = 0.0

    return BlogScore(
        tech_article_count=tech_count,
        total_article_count=total,
        avg_monthly_posts=round(avg_monthly, 2),
        avg_likes=round(avg_likes, 1),
        articles=scored_articles,
    )
