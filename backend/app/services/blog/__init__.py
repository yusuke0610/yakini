"""ブログ関連サービス。"""

from .collector import (
    BlogPlatformRequestError,
    UnsupportedBlogPlatformError,
    fetch_articles,
    fetch_note_articles,
    fetch_zenn_articles,
    verify_user_exists,
)
from .scorer import (
    ArticleWithTechFlag,
    BlogScore,
    blog_articles_to_score_dicts,
    calculate_blog_score,
    is_tech_article,
)

__all__ = [
    "ArticleWithTechFlag",
    "BlogPlatformRequestError",
    "BlogScore",
    "UnsupportedBlogPlatformError",
    "blog_articles_to_score_dicts",
    "calculate_blog_score",
    "fetch_articles",
    "fetch_note_articles",
    "fetch_zenn_articles",
    "is_tech_article",
    "verify_user_exists",
]
