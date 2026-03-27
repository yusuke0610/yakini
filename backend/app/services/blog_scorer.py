"""
ブログ記事のスコアリング（技術記事 S〜E ランク）。

技術系記事を判定し、投稿頻度・反応・記事数の3軸でランク付けする。
"""

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import date
from typing import List

logger = logging.getLogger(__name__)

_KEYWORDS_PATH = os.path.join(os.path.dirname(__file__), "blog_tech_keywords.json")

with open(_KEYWORDS_PATH, encoding="utf-8") as _f:
    _TECH_KEYWORDS: List[str] = json.load(_f)["keywords"]

# 大文字小文字を無視した比較用
_TECH_KEYWORDS_LOWER = [k.lower() for k in _TECH_KEYWORDS]

# ランク定義
RANKS = ["E", "D", "C", "B", "A", "S"]
RANK_VALUES = {r: i for i, r in enumerate(RANKS)}


@dataclass
class ArticleWithTechFlag:
    """技術記事判定結果付きの記事情報。"""

    id: str
    title: str
    url: str
    published_at: str | None
    likes_count: int
    tags: List[str]
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
    articles: List[ArticleWithTechFlag] = field(default_factory=list)


def is_tech_article(tags: List[str]) -> bool:
    """タグに技術系キーワードが含まれるか判定する。"""
    for tag in tags:
        tag_lower = tag.lower()
        for keyword in _TECH_KEYWORDS_LOWER:
            if keyword in tag_lower or tag_lower in keyword:
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
    """
    ブログ記事一覧からスコアリング結果を算出する。

    articles: BlogArticle のシリアライズ済みリスト
              各要素に id, title, url, published_at, likes_count, tags が必要。
    """
    scored_articles: List[ArticleWithTechFlag] = []
    tech_articles: List[dict] = []

    for art in articles:
        tags = art.get("tags", [])
        tech = is_tech_article(tags)
        scored_articles.append(ArticleWithTechFlag(
            id=art.get("id", ""),
            title=art.get("title", ""),
            url=art.get("url", ""),
            published_at=art.get("published_at"),
            likes_count=art.get("likes_count", 0),
            tags=tags,
            is_tech=tech,
        ))
        if tech:
            tech_articles.append(art)

    total = len(articles)
    tech_count = len(tech_articles)

    if tech_count == 0:
        return BlogScore(
            tech_article_count=0,
            total_article_count=total,
            articles=scored_articles,
        )

    # 平均いいね数
    total_likes = sum(a.get("likes_count", 0) for a in tech_articles)
    avg_likes = total_likes / tech_count

    # 月間平均投稿数
    dates = []
    for a in tech_articles:
        pub = a.get("published_at")
        if pub:
            try:
                dates.append(date.fromisoformat(pub))
            except (ValueError, TypeError):
                pass

    if dates:
        earliest = min(dates)
        today = date.today()
        months = max(
            (today.year - earliest.year) * 12 + (today.month - earliest.month),
            1,
        )
        avg_monthly = tech_count / months
    else:
        avg_monthly = 0.0

    freq_rank = _calc_frequency_rank(avg_monthly)
    react_rank = _calc_reaction_rank(avg_likes)
    count_rank = _calc_count_rank(tech_count)
    overall = _calc_overall_rank(freq_rank, react_rank, count_rank)

    return BlogScore(
        frequency_rank=freq_rank,
        reaction_rank=react_rank,
        count_rank=count_rank,
        overall_rank=overall,
        tech_article_count=tech_count,
        total_article_count=total,
        avg_monthly_posts=round(avg_monthly, 2),
        avg_likes=round(avg_likes, 1),
        articles=scored_articles,
    )
