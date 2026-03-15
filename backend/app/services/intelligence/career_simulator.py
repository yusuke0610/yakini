"""
Career simulation engine.

Simulates multiple possible career paths by traversing the career graph.
Returns branching paths with confidence scores.

Deterministic graph traversal — no LLM usage.
"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Set

from .career_paths import CAREER_ROLES
from .career_predictor import CareerPrediction
from .confidence_scorer import score_path
from .skill_growth_analyzer import SkillGrowth
from .skill_taxonomy import get_skill_category
from .skill_timeline_builder import SkillTimeline

logger = logging.getLogger(__name__)

MAX_PATH_DEPTH = 4
MAX_BRANCH_FACTOR = 3


@dataclass
class SimulatedPath:
    path: List[str]        # Sequence of role names
    confidence: float      # Overall path confidence (0.0 to 1.0)
    description: str       # Human-readable summary


@dataclass
class CareerSimulation:
    current_role: str
    paths: List[SimulatedPath]
    total_paths_explored: int


def simulate_careers(
    prediction: CareerPrediction,
    timelines: List[SkillTimeline],
    growth: List[SkillGrowth],
    max_paths: int = 5,
) -> CareerSimulation:
    """
    Simulate multiple career paths from the current predicted role.

    Uses depth-limited DFS on the career graph, scoring each path.
    """
    current = prediction.current_role.role_name
    user_skills: Set[str] = {t.skill_name for t in timelines}
    user_categories: Set[str] = {
        get_skill_category(s) for s in user_skills
    }
    growth_map: Dict[str, SkillGrowth] = {
        g.skill_name: g for g in growth
    }

    # DFS to find all paths
    all_paths: List[List[str]] = []
    _dfs(current, [current], set(), all_paths)

    # Score each path
    scored: List[SimulatedPath] = []
    for path in all_paths:
        if len(path) < 2:
            continue

        conf = score_path(
            path, user_skills, user_categories, growth_map,
        )
        desc = _generate_description(path)
        scored.append(SimulatedPath(
            path=path,
            confidence=conf,
            description=desc,
        ))

    scored.sort(key=lambda s: s.confidence, reverse=True)

    logger.info(
        "Simulated %d career paths from %s (showing top %d)",
        len(scored), current, max_paths,
    )

    return CareerSimulation(
        current_role=current,
        paths=scored[:max_paths],
        total_paths_explored=len(all_paths),
    )


def _dfs(
    role: str,
    current_path: List[str],
    visited: Set[str],
    all_paths: List[List[str]],
) -> None:
    """Depth-limited DFS on the career graph."""
    if len(current_path) >= MAX_PATH_DEPTH:
        all_paths.append(list(current_path))
        return

    role_def = CAREER_ROLES.get(role)
    if not role_def or not role_def.next_roles:
        all_paths.append(list(current_path))
        return

    visited.add(role)
    branches_taken = 0

    for next_role in role_def.next_roles:
        if next_role in visited:
            continue
        if branches_taken >= MAX_BRANCH_FACTOR:
            break

        current_path.append(next_role)
        _dfs(next_role, current_path, visited, all_paths)
        current_path.pop()
        branches_taken += 1

    # If no branches taken, save current path as terminal
    if branches_taken == 0:
        all_paths.append(list(current_path))

    visited.discard(role)


def _generate_description(path: List[str]) -> str:
    """Generate a human-readable path description."""
    if len(path) <= 1:
        return path[0] if path else ""

    parts: List[str] = []
    for i, role in enumerate(path):
        if i == 0:
            parts.append(f"Start as {role}")
        elif i == len(path) - 1:
            parts.append(f"target {role}")
        else:
            parts.append(f"grow into {role}")

    return ", ".join(parts)
