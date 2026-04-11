"""
GitHub リポジトリデータからの決定論的なスキル抽出。

以下の方法でスキルを抽出します：
  1. 言語検出 (GitHub の linguist)
  2. リポジトリのトピック
  3. 説明文のキーワードマッチング
  4. 依存関係分析 (requirements.txt, package.json など)
  5. ルートファイル / ディレクトリ検出 (Dockerfile, .github, terraform など)

LLMは使用しません。
"""

import logging
from dataclasses import dataclass, field
from typing import List, Set

from .github_collector import (
    DEPENDENCY_TO_FRAMEWORK,
    RepoData,
)
from .skill_taxonomy import (
    DESCRIPTION_KEYWORDS,
    LANGUAGE_TO_SKILL,
    TOPIC_TO_SKILLS,
    get_skill_category,
)

logger = logging.getLogger(__name__)


@dataclass
class ExtractedSkill:
    """単一のリポジトリから抽出されたスキル。"""

    skill_name: str
    category: str
    source: str  # "language", "topic", "description" など
    repo_name: str
    repo_created_at: str
    repo_pushed_at: str
    language_bytes: int = 0  # リポジトリ内のこの言語のバイト数


@dataclass
class ExtractionResult:
    skills: List[ExtractedSkill]
    repos_analyzed: int
    unique_skills: Set[str] = field(default_factory=set)


def extract_skills(repos: List[RepoData]) -> ExtractionResult:
    """
    GitHub リポジトリのリストからスキルを抽出します。

    すべてのリポジトリにわたるすべてのスキルの観測結果を返します
    （1つのスキルが異なるリポジトリから複数回現れる場合があります）。
    """
    all_skills: List[ExtractedSkill] = []
    unique: Set[str] = set()

    for repo in repos:
        repo_skills = _extract_from_repo(repo)
        all_skills.extend(repo_skills)
        for s in repo_skills:
            unique.add(s.skill_name)

    logger.info(
        "Extracted %d skill observations (%d unique) from %d repos",
        len(all_skills),
        len(unique),
        len(repos),
    )
    return ExtractionResult(
        skills=all_skills,
        repos_analyzed=len(repos),
        unique_skills=unique,
    )


def _extract_from_repo(repo: RepoData) -> List[ExtractedSkill]:
    """単一のリポジトリからスキルを抽出します。"""
    skills: List[ExtractedSkill] = []
    seen: Set[str] = set()

    # 1. 言語
    for lang, byte_count in repo.languages.items():
        skill_name = LANGUAGE_TO_SKILL.get(lang)
        if skill_name and skill_name not in seen:
            seen.add(skill_name)
            skills.append(
                ExtractedSkill(
                    skill_name=skill_name,
                    category=get_skill_category(skill_name),
                    source="language",
                    repo_name=repo.name,
                    repo_created_at=repo.created_at,
                    repo_pushed_at=repo.pushed_at,
                    language_bytes=byte_count,
                )
            )

    # 2. トピック
    for topic in repo.topics:
        topic_lower = topic.lower()
        matched_skills = TOPIC_TO_SKILLS.get(topic_lower, [])
        for skill_name in matched_skills:
            if skill_name not in seen:
                seen.add(skill_name)
                skills.append(
                    ExtractedSkill(
                        skill_name=skill_name,
                        category=get_skill_category(skill_name),
                        source="topic",
                        repo_name=repo.name,
                        repo_created_at=repo.created_at,
                        repo_pushed_at=repo.pushed_at,
                    )
                )

    # 3. 説明文のキーワード
    if repo.description:
        desc_lower = repo.description.lower()
        for keyword, matched_skills in DESCRIPTION_KEYWORDS.items():
            if keyword in desc_lower:
                for skill_name in matched_skills:
                    if skill_name not in seen:
                        seen.add(skill_name)
                        skills.append(
                            ExtractedSkill(
                                skill_name=skill_name,
                                category=get_skill_category(skill_name),
                                source="description",
                                repo_name=repo.name,
                                repo_created_at=repo.created_at,
                                repo_pushed_at=repo.pushed_at,
                            )
                        )

    # 4. 依存関係 (requirements.txt, package.json などから解析)
    for dep in repo.dependencies:
        framework = DEPENDENCY_TO_FRAMEWORK.get(dep)
        if framework and framework not in seen:
            seen.add(framework)
            skills.append(
                ExtractedSkill(
                    skill_name=framework,
                    category=get_skill_category(framework),
                    source="dependency",
                    repo_name=repo.name,
                    repo_created_at=repo.created_at,
                    repo_pushed_at=repo.pushed_at,
                )
            )

    # 5. ルートファイル / ディレクトリ検出
    for framework in repo.detected_frameworks:
        if framework not in seen:
            seen.add(framework)
            skills.append(
                ExtractedSkill(
                    skill_name=framework,
                    category=get_skill_category(framework),
                    source="root_file",
                    repo_name=repo.name,
                    repo_created_at=repo.created_at,
                    repo_pushed_at=repo.pushed_at,
                )
            )

    return skills
