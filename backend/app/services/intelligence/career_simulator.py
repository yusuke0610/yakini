"""
キャリアシミュレーションエンジン。

キャリアグラフを走査することで、複数の可能なキャリアパスをシミュレーションします。
信頼スコアとともに分岐するパスを返します。

決定論的なグラフ走査 — LLMは使用しません。
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
    path: List[str]        # ロール名のシーケンス
    confidence: float      # パス全体の信頼度 (0.0 から 1.0)
    description: str       # 人間が読める形式のサマリー


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
    現在の予測ロールから複数のキャリアパスをシミュレーションします。

    キャリアグラフ上で深さ制限付きの深さ優先探索（DFS）を使用し、各パスをスコアリングします。
    """
    current = prediction.current_role.role_name
    user_skills: Set[str] = {t.skill_name for t in timelines}
    user_categories: Set[str] = {
        get_skill_category(s) for s in user_skills
    }
    growth_map: Dict[str, SkillGrowth] = {
        g.skill_name: g for g in growth
    }

    # すべてのパスを見つけるための DFS
    all_paths: List[List[str]] = []
    _dfs(current, [current], set(), all_paths)

    # 各パスをスコアリング
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
    """キャリアグラフ上の深さ制限付き DFS。"""
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

    # 分岐が発生しなかった場合、現在のパスを終端として保存
    if branches_taken == 0:
        all_paths.append(list(current_path))

    visited.discard(role)


def _generate_description(path: List[str]) -> str:
    """人間が読める形式のパス説明を生成します。"""
    if len(path) <= 1:
        return path[0] if path else ""

    parts: List[str] = []
    for i, role in enumerate(path):
        if i == 0:
            parts.append(f"{role}として開始")
        elif i == len(path) - 1:
            parts.append(f"目標: {role}")
        else:
            parts.append(f"{role}へ成長")

    return " -> ".join(parts)
