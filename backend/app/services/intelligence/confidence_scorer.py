"""
キャリアパスの信頼度スコアリング。

以下の要素に基づいてキャリアパスをスコアリングします：
  - パス内の各ロールとのスキルの適合性
  - スキルの成長速度（台頭中のスキルは信頼度を向上させる）
  - カテゴリのカバレッジの広さ

決定論的 — LLMは使用しません。
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
    現在のスキル適合性と成長に基づいてキャリアパスをスコアリングします。

    0.0 から 1.0 の間の信頼度スコアを返します。
    """
    if len(path) < 2:
        return 0.0

    # パス内の各遷移をスコアリング
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

        # 距離減衰を適用：遠いロールほど不確実性が高まる
        decay = 1.0 / (1.0 + i * 0.4)
        transition_scores.append(score * decay)

    if not transition_scores:
        return 0.0

    # 加重平均：初期のロールに高い重みを置く
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
    """ユーザーのスキルがロールの定義にどの程度適合するかをスコアリングします。"""
    if not required_skills and not required_categories:
        # Engineering Manager のようなロール — 広さをベースにする
        return min(len(user_categories) / 5, 1.0) * 0.4

    req_set = set(required_skills)
    overlap = user_skills & req_set

    # 基本的なスキルの適合
    skill_score = len(overlap) / max(len(req_set), 1)

    # カテゴリのカバレッジ
    cat_set = set(required_categories)
    cat_overlap = user_categories & cat_set
    cat_score = len(cat_overlap) / max(len(cat_set), 1)

    # 台頭中のスキルのボーナス
    emerging_bonus = 0.0
    for skill in req_set - user_skills:
        # ユーザーがこのスキルのカテゴリに向かって成長しているかを確認
        for g in growth_map.values():
            if g.trend == GrowthTrend.EMERGING and skill in req_set:
                emerging_bonus += 0.05
                break

    return min(
        skill_score * 0.5 + cat_score * 0.35 + emerging_bonus,
        1.0,
    )
