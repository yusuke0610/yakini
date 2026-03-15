"""
Career prediction engine.

Predicts current role and likely next roles based on:
  - Skill graph alignment with role definitions
  - Skill growth velocity
  - Category coverage

Deterministic inference rules — LLM only for summarization (optional).
"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Set

from .career_paths import (
    CAREER_ROLES,
    RoleMatch,
    match_skills_to_roles,
)
from .skill_growth_analyzer import GrowthTrend, SkillGrowth
from .skill_taxonomy import get_skill_category
from .skill_timeline_builder import SkillTimeline

logger = logging.getLogger(__name__)


@dataclass
class PredictedRole:
    role_name: str
    confidence: float       # 0.0 to 1.0
    matching_skills: List[str]
    missing_skills: List[str]
    seniority: int


@dataclass
class CareerPrediction:
    current_role: PredictedRole
    next_roles: List[PredictedRole]
    long_term_roles: List[PredictedRole]
    skill_summary: Dict[str, List[str]]  # category → skills


def predict_career(
    timelines: List[SkillTimeline],
    growth: List[SkillGrowth],
) -> CareerPrediction:
    """
    Predict career trajectory from skill data.

    1. Match current skills to role definitions
    2. Identify best-fit current role
    3. Predict next and long-term roles via the career graph
    """
    # Build skill sets
    user_skills: Set[str] = {t.skill_name for t in timelines}
    user_categories: Set[str] = {
        get_skill_category(s) for s in user_skills
    }

    # Build growth lookup
    growth_map: Dict[str, SkillGrowth] = {
        g.skill_name: g for g in growth
    }
    emerging_skills = {
        g.skill_name for g in growth
        if g.trend == GrowthTrend.EMERGING
    }

    # 1. Match skills to all roles
    matches = match_skills_to_roles(user_skills, user_categories)
    if not matches:
        return _empty_prediction(user_skills)

    # 2. Current role: best match
    best_match = matches[0]
    current = _match_to_predicted_role(best_match, user_skills)

    # 3. Next roles: from current role's next_roles, scored
    current_role_def = CAREER_ROLES.get(best_match.role_name)
    next_role_names = (
        current_role_def.next_roles if current_role_def else []
    )

    next_roles = _score_next_roles(
        next_role_names, user_skills, user_categories,
        emerging_skills, growth_map,
    )

    # 4. Long-term roles: follow the graph 2 hops
    long_term_names: Set[str] = set()
    for nr in next_roles:
        role_def = CAREER_ROLES.get(nr.role_name)
        if role_def:
            long_term_names.update(role_def.next_roles)
    long_term_names -= {current.role_name}
    long_term_names -= {nr.role_name for nr in next_roles}

    long_term_roles = _score_next_roles(
        list(long_term_names), user_skills, user_categories,
        emerging_skills, growth_map, depth_penalty=0.5,
    )

    # Skill summary by category
    skill_summary: Dict[str, List[str]] = {}
    for skill in sorted(user_skills):
        cat = get_skill_category(skill)
        skill_summary.setdefault(cat, []).append(skill)

    return CareerPrediction(
        current_role=current,
        next_roles=next_roles[:5],
        long_term_roles=long_term_roles[:5],
        skill_summary=skill_summary,
    )


def _match_to_predicted_role(
    match: RoleMatch,
    user_skills: Set[str],
) -> PredictedRole:
    """Convert a RoleMatch to PredictedRole."""
    role_def = CAREER_ROLES.get(match.role_name)
    required = set(role_def.required_skills) if role_def else set()
    missing = sorted(required - user_skills)
    seniority = role_def.seniority if role_def else 1

    return PredictedRole(
        role_name=match.role_name,
        confidence=round(match.match_score, 2),
        matching_skills=sorted(match.skill_overlap),
        missing_skills=missing,
        seniority=seniority,
    )


def _score_next_roles(
    role_names: List[str],
    user_skills: Set[str],
    user_categories: Set[str],
    emerging_skills: Set[str],
    growth_map: Dict[str, SkillGrowth],
    depth_penalty: float = 1.0,
) -> List[PredictedRole]:
    """
    Score and rank a list of potential next roles.

    Scoring considers:
      - Skill alignment (how many required skills already met)
      - Emerging skill bonus (growing toward the role)
      - Depth penalty for roles further in the future
    """
    scored: List[PredictedRole] = []

    for name in role_names:
        role_def = CAREER_ROLES.get(name)
        if not role_def:
            continue

        required = set(role_def.required_skills)
        overlap = user_skills & required
        missing = required - user_skills

        # Base score from skill match
        if required:
            base_score = len(overlap) / len(required)
        else:
            # Roles without specific required skills (e.g. Manager)
            # Score based on category breadth
            base_score = min(len(user_categories) / 4, 1.0) * 0.5

        # Bonus for emerging skills that match required skills
        emerging_match = emerging_skills & required
        emerging_bonus = len(emerging_match) * 0.1

        # Category coverage
        role_cats = set(role_def.required_categories)
        cat_score = (
            len(user_categories & role_cats) / len(role_cats)
            if role_cats else 0.3
        )

        confidence = min(
            (base_score * 0.5 + cat_score * 0.3 + emerging_bonus)
            * depth_penalty,
            1.0,
        )

        scored.append(PredictedRole(
            role_name=name,
            confidence=round(confidence, 2),
            matching_skills=sorted(overlap),
            missing_skills=sorted(missing),
            seniority=role_def.seniority,
        ))

    scored.sort(key=lambda r: r.confidence, reverse=True)
    return scored


def _empty_prediction(user_skills: Set[str]) -> CareerPrediction:
    """Return empty prediction when no roles match."""
    skill_summary: Dict[str, List[str]] = {}
    for skill in sorted(user_skills):
        cat = get_skill_category(skill)
        skill_summary.setdefault(cat, []).append(skill)

    return CareerPrediction(
        current_role=PredictedRole(
            role_name="Developer",
            confidence=0.0,
            matching_skills=[],
            missing_skills=[],
            seniority=1,
        ),
        next_roles=[],
        long_term_roles=[],
        skill_summary=skill_summary,
    )
