"""
GitHub REST API 呼び出しを担うモジュール。

リポジトリ一覧・言語情報・ファイル内容取得などの純粋な API 通信を行う。
"""

import logging
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)

GITHUB_API = "https://api.github.com"

# この年数以内にプッシュされたリポジトリのみを取得
_REPO_MAX_AGE_YEARS = 3

# これより小さいリポジトリはスキップ（バイト）
_REPO_MIN_SIZE_BYTES = 1024

# 特定のスキルを示すルートファイル/ディレクトリ
_INTERESTING_ROOT_FILES = {
    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    "package.json",
    "requirements.txt",
    "pyproject.toml",
    "pom.xml",
    "go.mod",
    "Makefile",
    "Gemfile",
    ".github",
    "terraform",
    ".terraform",
    "Jenkinsfile",
    ".gitlab-ci.yml",
    ".circleci",
}


class GitHubUserNotFoundError(Exception):
    """GitHub ユーザーが見つからない場合の例外。"""

    def __init__(self, username: str):
        self.username = username
        super().__init__(f"GitHub user not found: {username}")


async def fetch_repos_raw(
    client: httpx.AsyncClient,
    username: str,
    max_pages: int = 5,
) -> List[Dict[str, Any]]:
    """
    指定ユーザーの全パブリックリポジトリを取得する（ページネーションあり）。

    ユーザーが存在しない場合は GitHubUserNotFoundError を発生させる。
    """
    raw_repos: List[Dict[str, Any]] = []
    for page in range(1, max_pages + 1):
        resp = await client.get(
            f"/users/{username}/repos",
            params={
                "per_page": 100,
                "page": page,
                "sort": "pushed",
                "type": "owner",
            },
        )
        if resp.status_code == 404:
            raise GitHubUserNotFoundError(username)
        if resp.status_code == 403:
            logger.warning("GitHub API rate limit hit")
            break
        resp.raise_for_status()
        batch = resp.json()
        if not batch:
            break
        raw_repos.extend(batch)
    return raw_repos


async def fetch_languages(
    client: httpx.AsyncClient,
    owner: str,
    repo: str,
) -> Dict[str, int]:
    """リポジトリの言語バイト数を取得する。"""
    try:
        resp = await client.get(f"/repos/{owner}/{repo}/languages")
        if resp.status_code == 403:
            logger.warning("Rate limit on languages for %s/%s", owner, repo)
            return {}
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPError:
        logger.warning("Failed to fetch languages for %s/%s", owner, repo)
        return {}


async def fetch_root_files(
    client: httpx.AsyncClient,
    owner: str,
    repo: str,
) -> List[str]:
    """リポジトリのルートレベルの注目すべきファイル名/ディレクトリ名を取得する。"""
    try:
        resp = await client.get(f"/repos/{owner}/{repo}/contents/")
        if resp.status_code in (403, 404):
            return []
        resp.raise_for_status()
        items: List[Any] = resp.json()
        if not isinstance(items, list):
            return []
        return [
            item["name"]
            for item in items
            if isinstance(item, dict)
            and "name" in item
            and item["name"] in _INTERESTING_ROOT_FILES
        ]
    except httpx.HTTPError:
        logger.warning("Failed to fetch contents for %s/%s", owner, repo)
        return []


async def fetch_file_content(
    client: httpx.AsyncClient,
    owner: str,
    repo: str,
    path: str,
) -> Optional[str]:
    """リポジトリから生のファイルコンテンツをダウンロードする。"""
    try:
        resp = await client.get(
            f"/repos/{owner}/{repo}/contents/{path}",
            headers={"Accept": "application/vnd.github.raw+json"},
        )
        if resp.status_code in (403, 404):
            return None
        resp.raise_for_status()
        return resp.text
    except httpx.HTTPError:
        logger.warning(
            "Failed to fetch %s for %s/%s",
            path,
            owner,
            repo,
        )
        return None
