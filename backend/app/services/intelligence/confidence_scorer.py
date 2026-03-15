"""
Career path confidence scoring.

Scores career paths based on:
  - Skill alignment with each role in the path
  - Skill growth velocity (emerging skills boost confidence)
  - Category coverage breadth

Deterministic — no LLM usage.
"""

from typing import Dict, List, Set

from .career_paths import CAREER_ROLES
from .skill_growth_analyzer import GrowthTrend, SkillGrowth


def score_path(
    path: List[str],
    user_skills: Set[str],
    user_categories: Set[str],
    growth_map: Dict[str, SkillGrowth],
) -> float:
    """
    Score a career path based on current skill alignment and growth.

    Returns a confidence score between 0.0 and 1.0.
    """
    if len(path) < 2:
        return 0.0

    # Score each transition in the path
    transition_scores: List[float] = []
    for i in range(len(path)):
        role_name = path[i]
        role_def = CAREER_ROLES.get(role_name)
        if not role_def:
            transition_scores.append(0.0)
            continue

        score = _score_role_fit(
            role_def.required_skills,
            role_def.required_categories,
            user_skills,
            user_categories,
            growth_map,
        )

        # Apply distance decay: further roles are less certain
        decay = 1.0 / (1.0 + i * 0.4)
        transition_scores.append(score * decay)

    if not transition_scores:
        return 0.0

    # Weighted average: more weight on early roles
    total_weight = 0.0
    weighted_sum = 0.0
    for i, score in enumerate(transition_scores):
        weight = 1.0 / (1 + i * 0.3)
        weighted_sum += score * weight
        total_weight += weight

    confidence = weighted_sum / total_weight if total_weight > 0 else 0.0
    return round(min(confidence, 1.0), 2)


def _score_role_fit(
    required_skills: List[str],
    required_categories: List[str],
    user_skills: Set[str],
    user_categories: Set[str],
    growth_map: Dict[str, SkillGrowth],
) -> float:
    """Score how well user skills fit a role definition."""
    if not required_skills and not required_categories:
        # Roles like Engineering Manager — base on breadth
        return min(len(user_categories) / 5, 1.0) * 0.4

    req_set = set(required_skills)
    overlap = user_skills & req_set

    # Base skill match
    skill_score = len(overlap) / max(len(req_set), 1)

    # Category coverage
    cat_set = set(required_categories)
    cat_overlap = user_categories & cat_set
    cat_score = len(cat_overlap) / max(len(cat_set), 1)

    # Emerging skill bonus
    emerging_bonus = 0.0
    for skill in req_set - user_skills:
        # Check if user is growing toward this skill's category
        for g in growth_map.values():
            if g.trend == GrowthTrend.EMERGING and skill in req_set:
                emerging_bonus += 0.05
                break

    return min(
        skill_score * 0.5 + cat_score * 0.35 + emerging_bonus,
        1.0,
    )
