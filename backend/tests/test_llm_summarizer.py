"""
LLM サマライザー（app/services/intelligence/llm_summarizer.py）のユニットテスト。

対象モジュール: app.services.intelligence.llm_summarizer
テスト方針:
  - summarize_blog_articles / generate_learning_advice は外部 LLM をモック化してテスト
  - _build_blog_prompt / _build_learning_advice_prompt は純粋関数として直接テスト
  - PII マスキング・空記事・空スコア等の境界値を網羅する
"""

import asyncio
from unittest.mock import AsyncMock, patch

from app.services.intelligence.llm_summarizer import (
    _build_blog_prompt,
    _build_learning_advice_prompt,
    generate_learning_advice,
    summarize_blog_articles,
)
from app.services.llm.sanitizer import SanitizeContext


def _run(coro):
    """async 関数を同期的に実行するヘルパー。"""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# ── _build_blog_prompt ──────────────────────────────────────────────────


class TestBuildBlogPrompt:
    def test_empty_articles(self):
        """記事が空の場合でも最低限の情報が返ること。"""
        result = _build_blog_prompt([])
        assert "記事数: 0" in result

    def test_article_count_in_prompt(self):
        """記事数が正しくプロンプトに含まれること。"""
        articles = [
            {"title": "記事1", "tags": [], "summary": "", "likes_count": 0},
            {"title": "記事2", "tags": [], "summary": "", "likes_count": 0},
        ]
        result = _build_blog_prompt(articles)
        assert "記事数: 2" in result

    def test_title_included(self):
        """記事タイトルがプロンプトに含まれること。"""
        articles = [{"title": "FastAPI入門", "tags": [], "summary": "", "likes_count": 0}]
        result = _build_blog_prompt(articles)
        assert "FastAPI入門" in result

    def test_tags_included(self):
        """タグがプロンプトに含まれること。"""
        articles = [{"title": "記事", "tags": ["Python", "FastAPI"], "summary": "", "likes_count": 0}]
        result = _build_blog_prompt(articles)
        assert "Python" in result
        assert "FastAPI" in result

    def test_likes_count_included(self):
        """いいね数がプロンプトに含まれること。"""
        articles = [{"title": "人気記事", "tags": [], "summary": "", "likes_count": 100}]
        result = _build_blog_prompt(articles)
        assert "100" in result

    def test_likes_count_zero_not_shown(self):
        """いいね数 0 の場合、いいね情報が出力されないこと。"""
        articles = [{"title": "記事", "tags": [], "summary": "", "likes_count": 0}]
        result = _build_blog_prompt(articles)
        assert "いいね" not in result

    def test_summary_truncated_to_100_chars(self):
        """summary が 100 文字で切り捨てられること。"""
        long_summary = "a" * 200
        articles = [{"title": "記事", "tags": [], "summary": long_summary, "likes_count": 0}]
        result = _build_blog_prompt(articles)
        # summary のそのままの 200 文字は含まれないが 100 文字は含まれる
        assert "a" * 100 in result
        assert "a" * 101 not in result

    def test_max_30_articles(self):
        """30 件を超える記事は切り捨てられること。"""
        articles = [
            {"title": f"記事{i}", "tags": [], "summary": "", "likes_count": 0}
            for i in range(50)
        ]
        result = _build_blog_prompt(articles)
        assert "記事29" in result
        assert "記事30" not in result

    def test_sanitize_context_applied(self):
        """SanitizeContext が指定された場合にマスキングが適用されること（型チェック）。"""
        articles = [{"title": "テスト", "tags": [], "summary": "概要", "likes_count": 0}]
        ctx = SanitizeContext()
        result = _build_blog_prompt(articles, context=ctx)
        assert isinstance(result, str)
        assert len(result) > 0


# ── _build_learning_advice_prompt ────────────────────────────────────────


class TestBuildLearningAdvicePrompt:
    def _make_analysis(self, repos=5, skills=10, langs=None):
        return {
            "repos_analyzed": repos,
            "unique_skills": skills,
            "languages": langs or {"Python": 50000, "TypeScript": 30000},
        }

    def _make_scores(self, backend=70, frontend=30, missing=None):
        return {
            "backend": backend,
            "frontend": frontend,
            "fullstack": 40,
            "sre": 20,
            "cloud": 15,
            "missing_skills": missing or [],
        }

    def test_repos_analyzed_in_prompt(self):
        result = _build_learning_advice_prompt(self._make_analysis(), self._make_scores())
        assert "分析リポジトリ数: 5" in result

    def test_unique_skills_in_prompt(self):
        result = _build_learning_advice_prompt(self._make_analysis(), self._make_scores())
        assert "ユニークスキル数: 10" in result

    def test_languages_included(self):
        result = _build_learning_advice_prompt(
            self._make_analysis(langs={"Python": 100}), self._make_scores()
        )
        assert "Python" in result

    def test_position_scores_in_prompt(self):
        result = _build_learning_advice_prompt(
            self._make_analysis(), self._make_scores(backend=80)
        )
        assert "Backend: 80/100" in result

    def test_missing_skills_included(self):
        scores = self._make_scores(missing=["Kubernetes", "Terraform"])
        result = _build_learning_advice_prompt(self._make_analysis(), scores)
        assert "Kubernetes" in result
        assert "Terraform" in result

    def test_no_missing_skills_message(self):
        """不足スキルがない場合の専用メッセージが含まれること。"""
        result = _build_learning_advice_prompt(
            self._make_analysis(), self._make_scores(missing=[])
        )
        assert "不足スキルなし" in result

    def test_empty_languages(self):
        """言語が空でもエラーにならないこと。"""
        result = _build_learning_advice_prompt(
            self._make_analysis(langs={}), self._make_scores()
        )
        assert isinstance(result, str)

    def test_username_not_in_prompt(self):
        """プライバシー上、ユーザー名はプロンプトに含めないこと。"""
        analysis = {**self._make_analysis(), "username": "private_user_123"}
        result = _build_learning_advice_prompt(analysis, self._make_scores())
        assert "private_user_123" not in result


# ── summarize_blog_articles ──────────────────────────────────────────────


class TestSummarizeBlogArticles:
    def test_calls_llm_client_generate(self):
        """LLM クライアントの generate が呼ばれ、結果が返ること。"""
        mock_client = AsyncMock()
        mock_client.generate = AsyncMock(return_value="テスト要約テキスト")

        with patch("app.services.intelligence.llm_summarizer._client", mock_client):
            result = _run(
                summarize_blog_articles(
                    [{"title": "記事", "tags": [], "summary": "", "likes_count": 0}]
                )
            )

        assert result == "テスト要約テキスト"
        mock_client.generate.assert_called_once()

    def test_empty_articles(self):
        """記事が空でも LLM に渡してレスポンスを返すこと。"""
        mock_client = AsyncMock()
        mock_client.generate = AsyncMock(return_value="")

        with patch("app.services.intelligence.llm_summarizer._client", mock_client):
            result = _run(summarize_blog_articles([]))

        assert result == ""

    def test_llm_unavailable_returns_empty(self):
        """LLM が空文字列を返した場合、空文字列が返ること。"""
        mock_client = AsyncMock()
        mock_client.generate = AsyncMock(return_value="")

        with patch("app.services.intelligence.llm_summarizer._client", mock_client):
            result = _run(summarize_blog_articles([{"title": "記事", "tags": []}]))

        assert result == ""

    def test_system_prompt_and_user_prompt_passed(self):
        """system_prompt と user_prompt の両方が generate に渡されること。"""
        mock_client = AsyncMock()
        mock_client.generate = AsyncMock(return_value="要約")

        with patch("app.services.intelligence.llm_summarizer._client", mock_client):
            _run(summarize_blog_articles([{"title": "記事", "tags": []}]))

        call_args = mock_client.generate.call_args
        assert call_args is not None
        # 第1引数: system_prompt, 第2引数: user_prompt
        assert len(call_args.args) == 2
        system_prompt, user_prompt = call_args.args
        assert isinstance(system_prompt, str) and len(system_prompt) > 0
        assert isinstance(user_prompt, str) and len(user_prompt) > 0


# ── generate_learning_advice ─────────────────────────────────────────────


class TestGenerateLearningAdvice:
    def _make_analysis(self):
        return {
            "repos_analyzed": 10,
            "unique_skills": 15,
            "languages": {"Python": 80000},
        }

    def _make_scores(self):
        return {
            "backend": 75,
            "frontend": 25,
            "fullstack": 50,
            "sre": 30,
            "cloud": 20,
            "missing_skills": ["Kubernetes"],
        }

    def test_calls_llm_generate(self):
        """LLM クライアントの generate が呼ばれ、アドバイスが返ること。"""
        mock_client = AsyncMock()
        mock_client.generate = AsyncMock(return_value="学習アドバイスです")

        with patch("app.services.intelligence.llm_summarizer._client", mock_client):
            result = _run(generate_learning_advice(self._make_analysis(), self._make_scores()))

        assert result == "学習アドバイスです"
        mock_client.generate.assert_called_once()

    def test_llm_returns_empty(self):
        """LLM が空文字列を返した場合、空文字列が返ること。"""
        mock_client = AsyncMock()
        mock_client.generate = AsyncMock(return_value="")

        with patch("app.services.intelligence.llm_summarizer._client", mock_client):
            result = _run(generate_learning_advice(self._make_analysis(), self._make_scores()))

        assert result == ""

    def test_system_and_user_prompt_passed(self):
        """generate に system_prompt と user_prompt が渡されること。"""
        mock_client = AsyncMock()
        mock_client.generate = AsyncMock(return_value="アドバイス")

        with patch("app.services.intelligence.llm_summarizer._client", mock_client):
            _run(generate_learning_advice(self._make_analysis(), self._make_scores()))

        call_args = mock_client.generate.call_args
        system_prompt, user_prompt = call_args.args
        assert isinstance(system_prompt, str) and len(system_prompt) > 0
        assert "Backend" in user_prompt  # ポジションスコアが含まれること
