"""
GitHub data collector.

Fetches public repository data via the GitHub REST API.
Uses repo metadata (languages, topics, dates) to avoid excessive API calls.
"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)

GITHUB_API = "https://api.github.com"


@dataclass
class RepoData:
    name: str
    owner: str
    description: str
    languages: Dict[str, int]  # language → bytes
    topics: List[str]
    created_at: str  # ISO 8601
    pushed_at: str   # ISO 8601
    fork: bool
    stargazers_count: int
    default_branch: str


async def collect_repos(
    username: str,
    token: Optional[str] = None,
    include_forks: bool = False,
    max_pages: int = 5,
) -> List[RepoData]:
    """
    Fetch all public repositories for a GitHub user.

    Returns list of RepoData with language breakdowns.
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
        # 1. Fetch repo list (paginated)
        raw_repos = []
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

        # 2. For each repo, fetch language breakdown
        for raw in raw_repos:
            if raw.get("private"):
                continue
            if raw.get("fork") and not include_forks:
                continue

            languages = await _fetch_languages(
                client, raw["owner"]["login"], raw["name"]
            )

            repos.append(RepoData(
                name=raw["name"],
                owner=raw["owner"]["login"],
                description=raw.get("description") or "",
                languages=languages,
                topics=raw.get("topics") or [],
                created_at=raw.get("created_at", ""),
                pushed_at=raw.get("pushed_at", ""),
                fork=raw.get("fork", False),
                stargazers_count=raw.get("stargazers_count", 0),
                default_branch=raw.get("default_branch", "main"),
            ))

    logger.info(
        "Collected %d repos for %s (skipped forks: %s)",
        len(repos), username, not include_forks,
    )
    return repos


async def _fetch_languages(
    client: httpx.AsyncClient,
    owner: str,
    repo: str,
) -> Dict[str, int]:
    """Fetch language byte counts for a repository."""
    try:
        resp = await client.get(f"/repos/{owner}/{repo}/languages")
        if resp.status_code == 403:
            logger.warning("Rate limit on languages for %s/%s", owner, repo)
            return {}
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPError:
        logger.warning(
            "Failed to fetch languages for %s/%s", owner, repo
        )
        return {}


class GitHubUserNotFoundError(Exception):
    def __init__(self, username: str):
        self.username = username
        super().__init__(f"GitHub user not found: {username}")
