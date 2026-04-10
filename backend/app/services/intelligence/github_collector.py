"""
GitHub データコレクター（オーケストレーション層）。

GitHub REST API を介してパブリックリポジトリのデータを取得します。
実際の API 呼び出しは github.api_client、解析処理は github.repo_analyzer に委譲します。

後方互換性のため、このモジュールから直接インポートできるシンボルを再エクスポートします。
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

import httpx

from .github.api_client import (
    _REPO_MAX_AGE_YEARS,
    _REPO_MIN_SIZE_BYTES,
    GITHUB_API,
    GitHubUserNotFoundError,
    fetch_file_content,
    fetch_languages,
    fetch_repos_raw,
    fetch_root_files,
)
from .github.repo_analyzer import (
    DEPENDENCY_FILES as _DEPENDENCY_FILES,
)
from .github.repo_analyzer import (
    DEPENDENCY_TO_FRAMEWORK,
)
from .github.repo_analyzer import (
    detect_from_root_files as _detect_from_root_files,
)
from .github.repo_analyzer import (
    parse_go_mod as _parse_go_mod,
)
from .github.repo_analyzer import (
    parse_package_json as _parse_package_json,
)
from .github.repo_analyzer import (
    parse_pom_xml as _parse_pom_xml,
)
from .github.repo_analyzer import (
    parse_pyproject_toml as _parse_pyproject_toml,
)
from .github.repo_analyzer import (
    parse_requirements_txt as _parse_requirements_txt,
)

logger = logging.getLogger(__name__)

# 後方互換性のため公開シンボルとして再エクスポート
__all__ = [
    "RepoData",
    "collect_repos",
    "GitHubUserNotFoundError",
    "DEPENDENCY_TO_FRAMEWORK",
    "_detect_from_root_files",
    "_parse_requirements_txt",
    "_parse_pyproject_toml",
    "_parse_package_json",
    "_parse_pom_xml",
    "_parse_go_mod",
    "GITHUB_API",
]


@dataclass
class RepoData:
    """リポジトリデータを保持するデータクラス。"""

    name: str
    owner: str
    description: str
    languages: Dict[str, int]  # 言語 → バイト数
    topics: List[str]
    created_at: str  # ISO 8601 形式
    pushed_at: str  # ISO 8601 形式
    fork: bool
    stargazers_count: int
    default_branch: str
    dependencies: List[str] = field(default_factory=list)
    root_files: List[str] = field(default_factory=list)
    detected_frameworks: List[str] = field(default_factory=list)


async def _parse_dependencies(
    client: httpx.AsyncClient,
    owner: str,
    repo: str,
    root_files: List[str],
) -> List[str]:
    """依存関係ファイルを解析し、検出されたフレームワーク/ライブラリ名を返す。"""
    deps: List[str] = []

    for fname in root_files:
        if fname not in _DEPENDENCY_FILES:
            continue
        content = await fetch_file_content(client, owner, repo, fname)
        if not content:
            continue

        if fname == "requirements.txt":
            deps.extend(_parse_requirements_txt(content))
        elif fname == "pyproject.toml":
            deps.extend(_parse_pyproject_toml(content))
        elif fname == "package.json":
            deps.extend(_parse_package_json(content))
        elif fname == "pom.xml":
            deps.extend(_parse_pom_xml(content))
        elif fname == "go.mod":
            deps.extend(_parse_go_mod(content))

    return list(set(deps))


async def collect_repos(
    username: str,
    token: Optional[str] = None,
    include_forks: bool = False,
    max_pages: int = 5,
) -> List[RepoData]:
    """
    GitHub ユーザーのすべてのパブリックリポジトリを取得する。

    言語の内訳を含む RepoData のリストを返す。
    """
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    repos: List[RepoData] = []

    async with httpx.AsyncClient(
        base_url=GITHUB_API,
        headers=headers,
        timeout=30.0,
    ) as client:
        # 1. リポジトリリストの取得
        raw_repos = await fetch_repos_raw(client, username, max_pages)

        # 2. 各リポジトリについて、言語の内訳と構造を取得
        cutoff = datetime.now(timezone.utc).replace(
            year=datetime.now(timezone.utc).year - _REPO_MAX_AGE_YEARS,
        )
        for raw in raw_repos:
            if raw.get("private"):
                continue
            if raw.get("fork") and not include_forks:
                continue
            if raw.get("size", 0) < (_REPO_MIN_SIZE_BYTES // 1024):
                continue
            pushed = raw.get("pushed_at", "")
            if pushed and pushed[:10] < cutoff.strftime("%Y-%m-%d"):
                continue

            owner_login = raw["owner"]["login"]
            repo_name = raw["name"]

            languages = await fetch_languages(client, owner_login, repo_name)
            root_files = await fetch_root_files(client, owner_login, repo_name)
            dependencies = await _parse_dependencies(
                client, owner_login, repo_name, root_files
            )
            detected_frameworks = _detect_from_root_files(root_files)

            repos.append(
                RepoData(
                    name=repo_name,
                    owner=owner_login,
                    description=raw.get("description") or "",
                    languages=languages,
                    topics=raw.get("topics") or [],
                    created_at=raw.get("created_at", ""),
                    pushed_at=raw.get("pushed_at", ""),
                    fork=raw.get("fork", False),
                    stargazers_count=raw.get("stargazers_count", 0),
                    default_branch=raw.get("default_branch", "main"),
                    dependencies=dependencies,
                    root_files=root_files,
                    detected_frameworks=detected_frameworks,
                )
            )

    logger.info(
        "Collected %d repos for %s (skipped forks: %s)",
        len(repos),
        username,
        not include_forks,
    )
    return repos
