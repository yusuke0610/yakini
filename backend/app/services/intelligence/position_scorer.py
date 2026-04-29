"""
エンジニアポジションスコアの算出。

GitHubリポジトリデータから5軸（Backend / Frontend / Fullstack / SRE / Cloud）の
適性スコアを0-100で算出する。
"""

import json
import logging
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Set

from .github_collector import RepoData

logger = logging.getLogger(__name__)

_WEIGHTS_PATH = os.path.join(os.path.dirname(__file__), "position_weights.json")

with open(_WEIGHTS_PATH, encoding="utf-8") as _f:
    _WEIGHTS: Dict[str, Any] = json.load(_f)


@dataclass
class PositionScores:
    """5軸のポジションスコアと不足スキル情報。"""

    backend: int = 0
    frontend: int = 0
    fullstack: int = 0
    sre: int = 0
    cloud: int = 0
    missing_skills: List[str] = field(default_factory=list)


def calculate_position_scores(repos: List[RepoData]) -> PositionScores:
    """
    リポジトリデータから各ポジションのスコアを算出する。

    算出ロジック:
      1. 全リポジトリの言語バイト数を集計し、言語比率を計算
      2. 全リポジトリのトピック・ルートファイルを収集
      3. 各ポジション（backend/frontend/sre/cloud）の重み定義に基づきスコア算出
      4. fullstack = min(backend, frontend) * 0.6 + max(backend, frontend) * 0.4
      5. フルスタック要件との差分から不足スキルを特定
    """
    if not repos:
        return PositionScores(
            missing_skills=_get_all_requirements(),
        )

    # 全リポジトリの言語バイト数を集計
    lang_totals: Dict[str, int] = {}
    for repo in repos:
        for lang, bytes_count in repo.languages.items():
            lang_totals[lang] = lang_totals.get(lang, 0) + bytes_count

    total_bytes = sum(lang_totals.values()) or 1
    lang_ratios = {lang: b / total_bytes for lang, b in lang_totals.items()}

    # 全リポジトリのトピック・ルートファイルを収集
    all_topics: Set[str] = set()
    all_files: Set[str] = set()
    all_frameworks: Set[str] = set()
    for repo in repos:
        all_topics.update(t.lower() for t in repo.topics)
        all_files.update(repo.root_files)
        all_frameworks.update(repo.detected_frameworks)

    # 検出フレームワークを等価なトピックに展開してスコア算出に反映させる
    # （リポジトリに topic タグが無くても依存関係から推定できるようにする）
    for fw in all_frameworks:
        all_topics.update(_FRAMEWORK_TO_TOPICS.get(fw, ()))

    # 各ポジションのスコア算出
    backend = _calc_axis_score("backend", lang_ratios, all_topics, all_files)
    frontend = _calc_axis_score("frontend", lang_ratios, all_topics, all_files)
    sre = _calc_axis_score("sre", lang_ratios, all_topics, all_files)
    cloud = _calc_axis_score("cloud", lang_ratios, all_topics, all_files)

    # Fullstack: 弱い方に引っ張られる計算
    fs_min = min(backend, frontend)
    fs_max = max(backend, frontend)
    fullstack = int(fs_min * 0.6 + fs_max * 0.4)

    # 不足スキル分析
    detected_skills = _detect_owned_skills(
        lang_ratios, all_topics, all_files, all_frameworks,
    )
    missing = _find_missing_skills(detected_skills)

    return PositionScores(
        backend=backend,
        frontend=frontend,
        fullstack=fullstack,
        sre=sre,
        cloud=cloud,
        missing_skills=missing,
    )


def _calc_axis_score(
    axis: str,
    lang_ratios: Dict[str, float],
    topics: Set[str],
    files: Set[str],
) -> int:
    """
    単一ポジション軸のスコアを算出する。

    言語比率 × 重み（最大70点）+ トピックマッチ（最大20点）+ ファイルマッチ（最大10点）
    → 0-100 にクランプ。
    """
    cfg = _WEIGHTS.get(axis, {})

    # 言語スコア（最大70点）
    lang_weights = cfg.get("languages", {})
    lang_score = 0.0
    for lang, weight in lang_weights.items():
        ratio = lang_ratios.get(lang, 0.0)
        lang_score += ratio * weight
    # 言語スコアを0-70に正規化
    max_lang_weight = max(lang_weights.values()) if lang_weights else 1
    lang_score = min(lang_score / max_lang_weight * 70, 70)

    # トピックスコア（最大20点）
    cfg_topics = cfg.get("topics", [])
    if cfg_topics:
        matched_topics = sum(1 for t in cfg_topics if t in topics)
        topic_score = min(matched_topics / len(cfg_topics) * 60, 20)
    else:
        topic_score = 0.0

    # ファイルスコア（最大10点）
    cfg_files = cfg.get("files", [])
    if cfg_files:
        matched_files = sum(1 for f in cfg_files if f in files)
        file_score = min(matched_files / len(cfg_files) * 30, 10)
    else:
        file_score = 0.0

    raw = lang_score + topic_score + file_score
    return min(int(raw), 100)


# 言語バイト比率からスキルへのマッピング（1% 以上で保有とみなす）
_LANG_SKILL_MAP: Dict[str, str] = {
    "Python": "Python", "Java": "Java", "Go": "Go",
    "Rust": "Rust", "Ruby": "Ruby", "PHP": "PHP",
    "TypeScript": "TypeScript", "JavaScript": "JavaScript",
    "CSS": "CSS", "HTML": "HTML", "SCSS": "CSS",
    "HCL": "Terraform", "Shell": "Shell",
    "Kotlin": "Kotlin", "C#": "C#",
}

# GitHub トピックからスキルへのマッピング
_TOPIC_SKILL_MAP: Dict[str, str] = {
    "react": "React", "vue": "Vue", "angular": "Angular",
    "nextjs": "Next.js", "docker": "Docker",
    "kubernetes": "Kubernetes", "k8s": "Kubernetes",
    "terraform": "Terraform", "aws": "AWS",
    "gcp": "GCP", "azure": "Azure",
    "ci-cd": "CI/CD", "graphql": "GraphQL",
    "rest": "REST API", "api": "REST API",
    "database": "SQL", "sql": "SQL",
}

# リポジトリルートファイルからスキルへのマッピング
_FILE_SKILL_MAP: Dict[str, str] = {
    "Dockerfile": "Docker",
    "docker-compose.yml": "Docker",
    "docker-compose.yaml": "Docker",
    ".github": "CI/CD",
    "Jenkinsfile": "CI/CD",
    ".gitlab-ci.yml": "CI/CD",
    ".circleci": "CI/CD",
    "terraform": "Terraform",
    ".terraform": "Terraform",
}

# 検出フレームワーク → position_weights.json で参照されるトピック語のマッピング。
# リポジトリに topic タグが無いケースでも依存関係から推定できるよう、
# `_calc_axis_score` の topic 判定に合成的に注入する。
_FRAMEWORK_TO_TOPICS: Dict[str, tuple] = {
    # フロントエンド
    "React": ("react", "frontend", "web"),
    "React Native": ("react", "frontend"),
    "Next.js": ("nextjs", "react", "frontend", "web"),
    "Gatsby": ("gatsby", "react", "frontend"),
    "Remix": ("remix", "react", "frontend"),
    "Vue": ("vue", "frontend", "web"),
    "Nuxt.js": ("nuxt", "vue", "frontend"),
    "Angular": ("angular", "frontend", "web"),
    "Svelte": ("svelte", "frontend"),
    "Astro": ("astro", "frontend"),
    # バックエンド
    "FastAPI": ("fastapi", "api", "backend"),
    "Django": ("django", "backend", "api"),
    "Flask": ("flask", "backend"),
    "Express": ("express", "backend", "api"),
    "NestJS": ("nestjs", "backend", "api"),
    "Spring Boot": ("spring", "backend", "api"),
    "Gin": ("backend", "api"),
    "Echo": ("backend", "api"),
    "Fiber": ("backend", "api"),
    # データベース / API
    "PostgreSQL": ("database",),
    "MongoDB": ("database",),
    "Redis": ("database",),
    "GraphQL": ("graphql", "api"),
    # インフラ / SRE
    "Docker": ("docker",),
    "Docker Compose": ("docker",),
    "GitHub Actions": ("ci-cd",),
    "Jenkins": ("ci-cd",),
    "GitLab CI": ("ci-cd",),
    "CircleCI": ("ci-cd",),
    "Terraform": ("terraform", "iac"),
    # クラウド
    "AWS": ("aws", "cloud"),
    "GCP": ("gcp", "cloud"),
    "Azure": ("azure", "cloud"),
}


# 検出フレームワークからスキルへのマッピング
_FRAMEWORK_SKILL_MAP: Dict[str, str] = {
    "Docker": "Docker",
    "Docker Compose": "Docker",
    "GitHub Actions": "CI/CD",
    "Jenkins": "CI/CD",
    "GitLab CI": "CI/CD",
    "CircleCI": "CI/CD",
    "Terraform": "Terraform",
    # フロントエンドフレームワーク
    "React": "React",
    "React Native": "React",
    "Next.js": "React",
    "Gatsby": "React",
    "Remix": "React",
    "Vue": "Vue",
    "Nuxt.js": "Vue",
    "Angular": "Angular",
    "Svelte": "Svelte",
    "Astro": "Astro",
    # バックエンドフレームワーク
    "FastAPI": "REST API",
    "Django": "REST API",
    "Flask": "REST API",
    "Express": "REST API",
    "NestJS": "REST API",
    "Spring Boot": "REST API",
    "Gin": "REST API",
    "Echo": "REST API",
    "Fiber": "REST API",
    # データベース
    "PostgreSQL": "SQL",
    "MongoDB": "SQL",
    "Redis": "SQL",
    # クラウド SDK
    "AWS": "AWS",
    "GCP": "GCP",
    "Azure": "Azure",
    # GraphQL
    "GraphQL": "GraphQL",
}

# 言語比率がこの閾値以上で「保有」とみなす
_LANG_SKILL_THRESHOLD = 0.01


def _detect_owned_skills(
    lang_ratios: Dict[str, float],
    topics: Set[str],
    files: Set[str],
    frameworks: Set[str],
) -> Set[str]:
    """ユーザーが保有しているスキルを特定する。"""
    owned: Set[str] = set()

    for lang, skill in _LANG_SKILL_MAP.items():
        if lang_ratios.get(lang, 0) >= _LANG_SKILL_THRESHOLD:
            owned.add(skill)

    for topic, skill in _TOPIC_SKILL_MAP.items():
        if topic in topics:
            owned.add(skill)

    for fname, skill in _FILE_SKILL_MAP.items():
        if fname in files:
            owned.add(skill)

    for fw, skill in _FRAMEWORK_SKILL_MAP.items():
        if fw in frameworks:
            owned.add(skill)

    return owned


def _find_missing_skills(owned: Set[str]) -> List[str]:
    """フルスタック要件と保有スキルの差分を算出する。"""
    requirements = _WEIGHTS.get("fullstack_requirements", {})
    missing: List[str] = []

    # 要件チェック用マッピング
    # `React or Vue` は SPA フレームワーク系スキルがどれか一つあれば満たすものとする
    checks = {
        "Python or Java or Go": {"Python", "Java", "Go"},
        "REST API設計": {"REST API", "GraphQL"},
        "DB設計/SQL": {"SQL"},
        "TypeScript": {"TypeScript"},
        "React or Vue": {"React", "Vue", "Angular", "Svelte", "Astro"},
        "HTML/CSS": {"CSS", "HTML"},
        "Docker": {"Docker"},
        "CI/CD": {"CI/CD"},
        "Git workflow": {"CI/CD"},  # GitHub Actions等で代替
        "クラウドサービス(GCP/AWS/Azure)基礎": {"GCP", "AWS", "Azure"},
    }

    for category, req_list in requirements.items():
        for req in req_list:
            needed = checks.get(req, set())
            if needed and not (owned & needed):
                missing.append(req)

    return missing


def _get_all_requirements() -> List[str]:
    """全フルスタック要件をリストで返す（リポジトリ0件時用）。"""
    requirements = _WEIGHTS.get("fullstack_requirements", {})
    all_reqs: List[str] = []
    for req_list in requirements.values():
        all_reqs.extend(req_list)
    return all_reqs
