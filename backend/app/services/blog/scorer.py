"""
ブログ記事のスコアリング（技術記事 S〜E ランク）。

技術系記事を判定し、投稿頻度・反応・記事数の3軸でランク付けする。
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

RANKS = ["E", "D", "C", "B", "A", "S"]
RANK_VALUES = {rank: i for i, rank in enumerate(RANKS)}


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
    """ブログスコアリング結果。"""

    frequency_rank: str = "E"
    reaction_rank: str = "E"
    count_rank: str = "E"
    overall_rank: str = "E"
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


def _calc_frequency_rank(avg_monthly: float) -> str:
    """月間平均投稿数からランクを算出する。"""
    if avg_monthly >= 4:
        return "S"
    if avg_monthly >= 2:
        return "A"
    if avg_monthly >= 1:
        return "B"
    if avg_monthly >= 0.5:
        return "C"
    if avg_monthly >= 1 / 3:
        return "D"
    return "E"


def _calc_reaction_rank(avg_likes: float) -> str:
    """平均いいね数からランクを算出する。"""
    if avg_likes >= 50:
        return "S"
    if avg_likes >= 30:
        return "A"
    if avg_likes >= 15:
        return "B"
    if avg_likes >= 5:
        return "C"
    if avg_likes >= 1:
        return "D"
    return "E"


def _calc_count_rank(count: int) -> str:
    """技術記事総数からランクを算出する。"""
    if count >= 50:
        return "S"
    if count >= 30:
        return "A"
    if count >= 15:
        return "B"
    if count >= 8:
        return "C"
    if count >= 3:
        return "D"
    return "E"


def _calc_overall_rank(freq: str, react: str, count: str) -> str:
    """3軸のランクから総合ランクを算出する。"""
    avg = (RANK_VALUES[freq] + RANK_VALUES[react] + RANK_VALUES[count]) / 3
    if avg >= 4.5:
        return "S"
    if avg >= 3.5:
        return "A"
    if avg >= 2.5:
        return "B"
    if avg >= 1.5:
        return "C"
    if avg >= 0.5:
        return "D"
    return "E"


def calculate_blog_score(articles: list[dict]) -> BlogScore:
    """ブログ記事一覧からスコアリング結果を算出する。"""
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

    freq_rank = _calc_frequency_rank(avg_monthly)
    react_rank = _calc_reaction_rank(avg_likes)
    count_rank = _calc_count_rank(tech_count)

    return BlogScore(
        frequency_rank=freq_rank,
        reaction_rank=react_rank,
        count_rank=count_rank,
        overall_rank=_calc_overall_rank(freq_rank, react_rank, count_rank),
        tech_article_count=tech_count,
        total_article_count=total,
        avg_monthly_posts=round(avg_monthly, 2),
        avg_likes=round(avg_likes, 1),
        articles=scored_articles,
    )
