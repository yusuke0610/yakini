"""ブログ関連サービス。"""

from .collector import (
    BlogAccountNotFoundError,
    BlogPlatformRequestError,
    UnsupportedBlogPlatformError,
    fetch_articles,
    fetch_note_articles,
    fetch_zenn_articles,
    normalize_username,
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
    "BlogAccountNotFoundError",
    "BlogPlatformRequestError",
    "BlogScore",
    "UnsupportedBlogPlatformError",
    "blog_articles_to_score_dicts",
    "calculate_blog_score",
    "fetch_articles",
    "fetch_note_articles",
    "fetch_zenn_articles",
    "is_tech_article",
    "normalize_username",
    "verify_user_exists",
]
