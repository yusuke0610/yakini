"""
キャリア予測エンジン。

以下の要素に基づいて現在のロールと将来の可能性が高いロールを予測します：
  - ロール定義に対するスキルグラフの適合性
  - スキルの成長速度
  - カテゴリのカバレッジ

決定論的な推論ルールを使用 — LLMは要約のみに使用（オプション）。
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
    confidence: float  # 0.0 から 1.0
    matching_skills: List[str]
    missing_skills: List[str]
    seniority: int


@dataclass
class CareerPrediction:
    current_role: PredictedRole
    next_roles: List[PredictedRole]
    long_term_roles: List[PredictedRole]
    skill_summary: Dict[str, List[str]]  # カテゴリ → スキル


def predict_career(
    timelines: List[SkillTimeline],
    growth: List[SkillGrowth],
) -> CareerPrediction:
    """
    スキルデータからキャリアの軌跡を予測します。

    1. 現在のスキルをロール定義と照合する
    2. 最も適合する現在のロールを特定する
    3. キャリアグラフを介して次および長期的なロールを予測する
    """
    # スキルセットの構築
    user_skills: Set[str] = {t.skill_name for t in timelines}
    user_categories: Set[str] = {get_skill_category(s) for s in user_skills}

    # 成長データのルックアップを構築
    growth_map: Dict[str, SkillGrowth] = {g.skill_name: g for g in growth}
    emerging_skills = {g.skill_name for g in growth if g.trend == GrowthTrend.EMERGING}

    # 1. スキルをすべてのロールと照合する
    matches = match_skills_to_roles(user_skills, user_categories)
    if not matches:
        return _empty_prediction(user_skills)

    # 2. 現在のロール：最も一致するもの
    best_match = matches[0]
    current = _match_to_predicted_role(best_match, user_skills)

    # 3. 次のロール：現在のロールの next_roles からスコアリング
    current_role_def = CAREER_ROLES.get(best_match.role_name)
    next_role_names = current_role_def.next_roles if current_role_def else []

    next_roles = _score_next_roles(
        next_role_names,
        user_skills,
        user_categories,
        emerging_skills,
        growth_map,
    )

    # 4. 長期的なロール：グラフを2ホップ辿る
    long_term_names: Set[str] = set()
    for nr in next_roles:
        role_def = CAREER_ROLES.get(nr.role_name)
        if role_def:
            long_term_names.update(role_def.next_roles)
    long_term_names -= {current.role_name}
    long_term_names -= {nr.role_name for nr in next_roles}

    long_term_roles = _score_next_roles(
        list(long_term_names),
        user_skills,
        user_categories,
        emerging_skills,
        growth_map,
        depth_penalty=0.5,
    )

    # カテゴリ別のスキルサマリー
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
    """RoleMatch を PredictedRole に変換します。"""
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
    潜在的な次のロールのリストをスコアリングし、ランク付けします。

    スコアリングでは以下の要素を考慮します：
      - スキルの適合性（必要なスキルのうちいくつを満たしているか）
      - 台頭中のスキルのボーナス（ロールに向かって成長しているか）
      - 将来の遠いロールに対する深さのペナルティ
    """
    scored: List[PredictedRole] = []

    for name in role_names:
        role_def = CAREER_ROLES.get(name)
        if not role_def:
            continue

        required = set(role_def.required_skills)
        overlap = user_skills & required
        missing = required - user_skills

        # スキルの一致に基づく基本スコア
        if required:
            base_score = len(overlap) / len(required)
        else:
            # 特定の必須スキルがないロール（例：マネージャー）
            # カテゴリの広さに基づくスコア
            base_score = min(len(user_categories) / 4, 1.0) * 0.5

        # 必須スキルに一致する台頭中のスキルのボーナス
        emerging_match = emerging_skills & required
        emerging_bonus = len(emerging_match) * 0.1

        # カテゴリのカバレッジ
        role_cats = set(role_def.required_categories)
        cat_score = (
            len(user_categories & role_cats) / len(role_cats) if role_cats else 0.3
        )

        confidence = min(
            (base_score * 0.5 + cat_score * 0.3 + emerging_bonus) * depth_penalty,
            1.0,
        )

        scored.append(
            PredictedRole(
                role_name=name,
                confidence=round(confidence, 2),
                matching_skills=sorted(overlap),
                missing_skills=sorted(missing),
                seniority=role_def.seniority,
            )
        )

    scored.sort(key=lambda r: r.confidence, reverse=True)
    return scored


def _empty_prediction(user_skills: Set[str]) -> CareerPrediction:
    """一致するロールがない場合に空の予測を返します。"""
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
