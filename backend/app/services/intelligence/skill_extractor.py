"""
Deterministic skill extraction from GitHub repository data.

Extracts skills using:
  1. Language detection (GitHub's linguist)
  2. Repository topics
  3. Description keyword matching
  4. Dependency analysis (requirements.txt, package.json, etc.)
  5. Root file / directory detection (Dockerfile, .github, terraform, etc.)

No LLM usage.
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
    """A skill extracted from a single repository."""
    skill_name: str
    category: str
    source: str  # "language", "topic", or "description"
    repo_name: str
    repo_created_at: str
    repo_pushed_at: str
    language_bytes: int = 0  # bytes of this language in the repo


@dataclass
class ExtractionResult:
    skills: List[ExtractedSkill]
    repos_analyzed: int
    unique_skills: Set[str] = field(default_factory=set)


def extract_skills(repos: List[RepoData]) -> ExtractionResult:
    """
    Extract skills from a list of GitHub repositories.

    Returns all skill observations across all repos
    (one skill may appear multiple times from different repos).
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
        len(all_skills), len(unique), len(repos),
    )
    return ExtractionResult(
        skills=all_skills,
        repos_analyzed=len(repos),
        unique_skills=unique,
    )


def _extract_from_repo(repo: RepoData) -> List[ExtractedSkill]:
    """Extract skills from a single repository."""
    skills: List[ExtractedSkill] = []
    seen: Set[str] = set()

    # 1. Languages
    for lang, byte_count in repo.languages.items():
        skill_name = LANGUAGE_TO_SKILL.get(lang)
        if skill_name and skill_name not in seen:
            seen.add(skill_name)
            skills.append(ExtractedSkill(
                skill_name=skill_name,
                category=get_skill_category(skill_name),
                source="language",
                repo_name=repo.name,
                repo_created_at=repo.created_at,
                repo_pushed_at=repo.pushed_at,
                language_bytes=byte_count,
            ))

    # 2. Topics
    for topic in repo.topics:
        topic_lower = topic.lower()
        matched_skills = TOPIC_TO_SKILLS.get(topic_lower, [])
        for skill_name in matched_skills:
            if skill_name not in seen:
                seen.add(skill_name)
                skills.append(ExtractedSkill(
                    skill_name=skill_name,
                    category=get_skill_category(skill_name),
                    source="topic",
                    repo_name=repo.name,
                    repo_created_at=repo.created_at,
                    repo_pushed_at=repo.pushed_at,
                ))

    # 3. Description keywords
    if repo.description:
        desc_lower = repo.description.lower()
        for keyword, matched_skills in DESCRIPTION_KEYWORDS.items():
            if keyword in desc_lower:
                for skill_name in matched_skills:
                    if skill_name not in seen:
                        seen.add(skill_name)
                        skills.append(ExtractedSkill(
                            skill_name=skill_name,
                            category=get_skill_category(skill_name),
                            source="description",
                            repo_name=repo.name,
                            repo_created_at=repo.created_at,
                            repo_pushed_at=repo.pushed_at,
                        ))

    # 4. Dependencies (parsed from requirements.txt, package.json, etc.)
    for dep in repo.dependencies:
        framework = DEPENDENCY_TO_FRAMEWORK.get(dep)
        if framework and framework not in seen:
            seen.add(framework)
            skills.append(ExtractedSkill(
                skill_name=framework,
                category=get_skill_category(framework),
                source="dependency",
                repo_name=repo.name,
                repo_created_at=repo.created_at,
                repo_pushed_at=repo.pushed_at,
            ))

    # 5. Root file / directory detection
    for framework in repo.detected_frameworks:
        if framework not in seen:
            seen.add(framework)
            skills.append(ExtractedSkill(
                skill_name=framework,
                category=get_skill_category(framework),
                source="root_file",
                repo_name=repo.name,
                repo_created_at=repo.created_at,
                repo_pushed_at=repo.pushed_at,
            ))

    return skills
