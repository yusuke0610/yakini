"""パイプラインのユニットテスト。"""

import asyncio
from unittest.mock import AsyncMock, patch

from app.services.intelligence.github_collector import RepoData
from app.services.intelligence.pipeline import run_pipeline


def _make_repo(name, languages=None):
    return RepoData(
        name=name,
        owner="testuser",
        description="",
        languages=languages or {},
        topics=[],
        created_at="2024-01-01T00:00:00Z",
        pushed_at="2024-06-01T00:00:00Z",
        fork=False,
        stargazers_count=0,
        default_branch="main",
        dependencies=[],
        root_files=[],
        detected_frameworks=[],
    )


def test_run_pipeline_aggregates_languages() -> None:
    """複数リポジトリの言語バイト数が正しく集計されること。"""
    repos = [
        _make_repo("repo-a", {"Python": 10000, "JavaScript": 5000}),
        _make_repo("repo-b", {"Python": 20000, "Go": 8000}),
    ]

    with patch(
        "app.services.intelligence.pipeline.collect_repos",
        new_callable=AsyncMock,
        return_value=repos,
    ):
        result = asyncio.get_event_loop().run_until_complete(
            run_pipeline(username="testuser")
        )

    assert result.languages["Python"] == 30000
    assert result.languages["JavaScript"] == 5000
    assert result.languages["Go"] == 8000


def test_run_pipeline_empty_repos() -> None:
    """リポジトリ 0 件で正常終了すること。"""
    with patch(
        "app.services.intelligence.pipeline.collect_repos",
        new_callable=AsyncMock,
        return_value=[],
    ):
        result = asyncio.get_event_loop().run_until_complete(
            run_pipeline(username="emptyuser")
        )

    assert result.repos_analyzed == 0
    assert result.unique_skills == 0
    assert result.languages == {}
