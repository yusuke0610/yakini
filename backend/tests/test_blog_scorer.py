"""ブログスコアリングのユニットテスト。"""

from app.services.blog_scorer import (
    calculate_blog_score,
    is_tech_article,
)


def test_is_tech_article_with_matching_tag():
    """技術系タグがある場合、技術記事と判定されること。"""
    assert is_tech_article(["Python", "日記"])
    assert is_tech_article(["react", "frontend"])
    assert is_tech_article(["プログラミング"])
    assert is_tech_article(["AWS"])


def test_is_tech_article_case_insensitive():
    """大文字小文字を無視してマッチすること。"""
    assert is_tech_article(["python"])
    assert is_tech_article(["REACT"])
    assert is_tech_article(["TypeScript"])


def test_is_tech_article_partial_match():
    """部分一致でマッチすること。"""
    assert is_tech_article(["Web開発入門"])
    assert is_tech_article(["AI活用"])


def test_is_tech_article_no_match():
    """技術系タグがない場合、技術記事と判定されないこと。"""
    assert not is_tech_article(["日記", "旅行", "料理"])
    assert not is_tech_article([])


def test_empty_articles():
    """記事0件の場合、全ランクEであること。"""
    result = calculate_blog_score([])
    assert result.overall_rank == "E"
    assert result.frequency_rank == "E"
    assert result.reaction_rank == "E"
    assert result.count_rank == "E"
    assert result.tech_article_count == 0


def test_no_tech_articles():
    """技術記事0件の場合、全ランクEであること。"""
    articles = [
        {
            "id": "1",
            "title": "日記",
            "url": "https://example.com/1",
            "published_at": "2024-01-01",
            "likes_count": 100,
            "tags": ["日記", "旅行"],
        },
    ]
    result = calculate_blog_score(articles)
    assert result.overall_rank == "E"
    assert result.tech_article_count == 0
    assert result.total_article_count == 1


def test_frequency_rank_s():
    """月4回以上の投稿でSランクになること。"""
    # 1ヶ月で4記事 → S
    articles = [
        {
            "id": str(i),
            "title": f"Tech Article {i}",
            "url": f"https://example.com/{i}",
            "published_at": "2026-03-01",
            "likes_count": 50,
            "tags": ["Python"],
        }
        for i in range(4)
    ]
    result = calculate_blog_score(articles)
    assert result.frequency_rank == "S"


def test_reaction_rank():
    """平均いいね数に基づくランク算出が正しいこと。"""
    articles = [
        {
            "id": "1",
            "title": "Tech",
            "url": "https://example.com/1",
            "published_at": "2024-01-01",
            "likes_count": 60,
            "tags": ["Python"],
        },
    ]
    result = calculate_blog_score(articles)
    assert result.reaction_rank == "S"  # 60 >= 50


def test_count_rank():
    """技術記事数に基づくランク算出が正しいこと。"""
    articles = [
        {
            "id": str(i),
            "title": f"Tech {i}",
            "url": f"https://example.com/{i}",
            "published_at": "2024-01-01",
            "likes_count": 0,
            "tags": ["Python"],
        }
        for i in range(50)
    ]
    result = calculate_blog_score(articles)
    assert result.count_rank == "S"  # 50 >= 50


def test_overall_rank_calculation():
    """総合ランクが3軸の平均から算出されること。"""
    # 1件、いいね0、1ヶ月前の投稿
    articles = [
        {
            "id": "1",
            "title": "Tech",
            "url": "https://example.com/1",
            "published_at": "2026-03-01",
            "likes_count": 0,
            "tags": ["Python"],
        },
    ]
    result = calculate_blog_score(articles)
    # count_rank = E (1件), reaction_rank = E (0いいね)
    # frequency は1ヶ月で1回 → B
    # (3 + 0 + 0) / 3 = 1.0 → D
    assert result.overall_rank in ["D", "C", "E"]  # 頻度次第


def test_articles_flagged_correctly():
    """技術記事と非技術記事が正しくフラグ付けされること。"""
    articles = [
        {
            "id": "1",
            "title": "Python入門",
            "url": "https://example.com/1",
            "published_at": "2024-01-01",
            "likes_count": 10,
            "tags": ["Python"],
        },
        {
            "id": "2",
            "title": "旅行日記",
            "url": "https://example.com/2",
            "published_at": "2024-01-01",
            "likes_count": 5,
            "tags": ["旅行"],
        },
    ]
    result = calculate_blog_score(articles)
    assert result.tech_article_count == 1
    assert result.total_article_count == 2
    tech_flags = {a.id: a.is_tech for a in result.articles}
    assert tech_flags["1"] is True
    assert tech_flags["2"] is False


def test_avg_likes_calculation():
    """平均いいね数が正しく計算されること。"""
    articles = [
        {
            "id": str(i),
            "title": f"Tech {i}",
            "url": f"https://example.com/{i}",
            "published_at": "2024-01-01",
            "likes_count": likes,
            "tags": ["Python"],
        }
        for i, likes in enumerate([10, 20, 30])
    ]
    result = calculate_blog_score(articles)
    assert result.avg_likes == 20.0
