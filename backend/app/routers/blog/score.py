"""ブログスコアリング エンドポイント。"""

from dataclasses import asdict

from fastapi import APIRouter, Depends

from ...core.security.auth import get_current_user
from ...db import get_db
from ...models import User
from ...repositories import BlogArticleRepository
from ...schemas import BlogScoreResponse
from ...services.blog.scorer import blog_articles_to_score_dicts, calculate_blog_score

router = APIRouter()


@router.get("/score", response_model=BlogScoreResponse)
def get_blog_score(
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """保存済みの記事に対してスコアリングを実行する。"""
    repo = BlogArticleRepository(db, user.id)
    articles = repo.list_by_user()

    score = calculate_blog_score(blog_articles_to_score_dicts(articles))
    return BlogScoreResponse.model_validate(asdict(score))
