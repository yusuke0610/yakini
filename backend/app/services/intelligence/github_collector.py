"""
GitHub data collector.

Fetches public repository data via the GitHub REST API.
Uses repo metadata (languages, topics, dates) to avoid excessive API calls.
Repository structure analysis (root files, dependencies) enriches skill detection.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)

GITHUB_API = "https://api.github.com"

# Only fetch repos pushed within this many years
_REPO_MAX_AGE_YEARS = 3

# Skip repos smaller than this (bytes)
_REPO_MIN_SIZE_BYTES = 1024

# Root files/dirs that indicate specific skills
_INTERESTING_ROOT_FILES = {
    "Dockerfile", "docker-compose.yml", "docker-compose.yaml",
    "package.json", "requirements.txt", "pyproject.toml",
    "pom.xml", "go.mod", "Makefile", "Gemfile",
    ".github", "terraform", ".terraform",
    "Jenkinsfile", ".gitlab-ci.yml", ".circleci",
}

# Dependency file → parser function name
_DEPENDENCY_FILES = {
    "requirements.txt",
    "pyproject.toml",
    "package.json",
    "pom.xml",
    "go.mod",
}


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
    dependencies: List[str] = field(default_factory=list)
    root_files: List[str] = field(default_factory=list)
    detected_frameworks: List[str] = field(default_factory=list)


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

        # 2. For each repo, fetch language breakdown + structure
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

            languages = await _fetch_languages(
                client, owner_login, repo_name,
            )
            root_files = await _fetch_root_files(
                client, owner_login, repo_name,
            )
            dependencies = await _parse_dependencies(
                client, owner_login, repo_name, root_files,
            )
            detected_frameworks = _detect_from_root_files(root_files)

            repos.append(RepoData(
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


async def _fetch_root_files(
    client: httpx.AsyncClient,
    owner: str,
    repo: str,
) -> List[str]:
    """Fetch root-level file and directory names for a repository."""
    try:
        resp = await client.get(f"/repos/{owner}/{repo}/contents/")
        if resp.status_code in (403, 404):
            return []
        resp.raise_for_status()
        items: List[Any] = resp.json()
        if not isinstance(items, list):
            return []
        return [
            item["name"] for item in items
            if isinstance(item, dict) and "name" in item
            and item["name"] in _INTERESTING_ROOT_FILES
        ]
    except httpx.HTTPError:
        logger.warning("Failed to fetch contents for %s/%s", owner, repo)
        return []


async def _fetch_file_content(
    client: httpx.AsyncClient,
    owner: str,
    repo: str,
    path: str,
) -> Optional[str]:
    """Download raw file content from a repository."""
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
            "Failed to fetch %s for %s/%s", path, owner, repo,
        )
        return None


async def _parse_dependencies(
    client: httpx.AsyncClient,
    owner: str,
    repo: str,
    root_files: List[str],
) -> List[str]:
    """Parse dependency files and return detected framework/library names."""
    deps: List[str] = []

    for fname in root_files:
        if fname not in _DEPENDENCY_FILES:
            continue
        content = await _fetch_file_content(client, owner, repo, fname)
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


def _parse_requirements_txt(content: str) -> List[str]:
    """Extract package names from requirements.txt."""
    packages: List[str] = []
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue
        # Strip version specifiers: pkg>=1.0, pkg==1.0, pkg[extra]
        name = line.split(">=")[0].split("<=")[0].split("==")[0]
        name = name.split("!=")[0].split("~=")[0].split(">")[0].split("<")[0]
        name = name.split("[")[0].split(";")[0].strip()
        if name:
            packages.append(name.lower())
    return packages


def _parse_pyproject_toml(content: str) -> List[str]:
    """Extract dependency names from pyproject.toml (simple line-based)."""
    packages: List[str] = []
    in_deps = False
    for line in content.splitlines():
        stripped = line.strip()
        if stripped in (
            "[project.dependencies]",
            "[tool.poetry.dependencies]",
            "dependencies = [",
        ):
            in_deps = True
            continue
        if in_deps:
            if stripped.startswith("[") or (
                not stripped.startswith('"')
                and not stripped.startswith("'")
                and "=" in stripped
                and not stripped.startswith("#")
                and "]" not in stripped
            ):
                # poetry style: name = "^1.0"
                name = stripped.split("=")[0].strip().lower()
                if name and name != "python":
                    packages.append(name)
                continue
            if stripped.startswith('"') or stripped.startswith("'"):
                # PEP 621 style: "fastapi>=0.100"
                name = stripped.strip("\"', ")
                name = name.split(">=")[0].split("<=")[0].split("==")[0]
                name = name.split("!=")[0].split("~=")[0].split(">")[0]
                name = name.split("<")[0].split("[")[0].split(";")[0].strip()
                if name:
                    packages.append(name.lower())
                continue
            if stripped == "]" or (
                stripped.startswith("[") and stripped != "]"
            ):
                in_deps = False
    return packages


def _parse_package_json(content: str) -> List[str]:
    """Extract dependency names from package.json."""
    import json
    try:
        data = json.loads(content)
    except (json.JSONDecodeError, ValueError):
        return []
    packages: List[str] = []
    for key in ("dependencies", "devDependencies"):
        deps = data.get(key)
        if isinstance(deps, dict):
            packages.extend(dep.lower() for dep in deps)
    return packages


def _parse_pom_xml(content: str) -> List[str]:
    """Extract artifactId values from pom.xml (basic regex)."""
    import re
    return [
        m.lower()
        for m in re.findall(r"<artifactId>([^<]+)</artifactId>", content)
    ]


def _parse_go_mod(content: str) -> List[str]:
    """Extract module paths from go.mod require block."""
    modules: List[str] = []
    in_require = False
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("require ("):
            in_require = True
            continue
        if in_require:
            if stripped == ")":
                in_require = False
                continue
            parts = stripped.split()
            if parts:
                modules.append(parts[0].lower())
    return modules


# ── Dependency → Framework mapping ────────────────────────────────────

DEPENDENCY_TO_FRAMEWORK: Dict[str, str] = {
    # Python
    "fastapi": "FastAPI",
    "django": "Django",
    "flask": "Flask",
    "sqlalchemy": "SQLAlchemy",
    "pandas": "Pandas",
    "numpy": "NumPy",
    "scikit-learn": "scikit-learn",
    "sklearn": "scikit-learn",
    "tensorflow": "TensorFlow",
    "torch": "PyTorch",
    "pytorch": "PyTorch",
    "langchain": "LangChain",
    "celery": "Celery",
    "airflow": "Airflow",
    "apache-airflow": "Airflow",
    "mlflow": "MLflow",
    "sentry-sdk": "Sentry",
    "prometheus-client": "Prometheus",
    "boto3": "AWS",
    "google-cloud-storage": "GCP",
    "azure-storage-blob": "Azure",
    # Node
    "react": "React",
    "react-dom": "React",
    "next": "Next.js",
    "vue": "Vue",
    "nuxt": "Nuxt.js",
    "angular": "Angular",
    "@angular/core": "Angular",
    "svelte": "Svelte",
    "express": "Express",
    "@nestjs/core": "NestJS",
    "gatsby": "Gatsby",
    "remix": "Remix",
    "astro": "Astro",
    "react-native": "React Native",
    "prisma": "PostgreSQL",
    "mongoose": "MongoDB",
    "redis": "Redis",
    "ioredis": "Redis",
    "graphql": "GraphQL",
    "@apollo/server": "GraphQL",
    # Java (artifactId)
    "spring-boot": "Spring Boot",
    "spring-boot-starter": "Spring Boot",
    "spring-boot-starter-web": "Spring Boot",
    # Go
    "github.com/gin-gonic/gin": "Gin",
    "github.com/labstack/echo": "Echo",
    "github.com/gofiber/fiber": "Fiber",
}


# ── Root file → Skill mapping ─────────────────────────────────────────

_ROOT_FILE_SKILLS: Dict[str, str] = {
    "Dockerfile": "Docker",
    "docker-compose.yml": "Docker Compose",
    "docker-compose.yaml": "Docker Compose",
    ".github": "GitHub Actions",
    "terraform": "Terraform",
    ".terraform": "Terraform",
    "Makefile": "Build Automation",
    "Jenkinsfile": "Jenkins",
    ".gitlab-ci.yml": "GitLab CI",
    ".circleci": "CircleCI",
    "go.mod": "Go",
    "Gemfile": "Ruby",
}


def _detect_from_root_files(root_files: List[str]) -> List[str]:
    """Detect skills from root-level files and directories."""
    detected: List[str] = []
    seen: set = set()
    for fname in root_files:
        skill = _ROOT_FILE_SKILLS.get(fname)
        if skill and skill not in seen:
            seen.add(skill)
            detected.append(skill)
    return detected


class GitHubUserNotFoundError(Exception):
    def __init__(self, username: str):
        self.username = username
        super().__init__(f"GitHub user not found: {username}")
