"""スキル → ロールマッチングロジック。"""

from dataclasses import dataclass
from typing import List, Set

from .definitions import CAREER_ROLES


@dataclass
class RoleMatch:
    """ロールマッチング結果を保持するデータクラス。"""

    role_name: str
    skill_overlap: Set[str]
    category_coverage: float
    match_score: float


def match_skills_to_roles(
    user_skills: Set[str],
    user_categories: Set[str],
) -> List[RoleMatch]:
    """ユーザーのスキルが各ロール定義とどの程度一致するかをスコアリングする。

    スキルの一致度 60% + カテゴリのカバー率 40% で重み付けスコアを算出する。
    """
    matches: List[RoleMatch] = []

    for name, role in CAREER_ROLES.items():
        if not role.required_skills and not role.required_categories:
            continue

        # スキルの重複
        role_skills = set(role.required_skills)
        overlap = user_skills & role_skills
        skill_score = len(overlap) / max(len(role_skills), 1)

        # カテゴリのカバー率
        role_cats = set(role.required_categories)
        cat_overlap = user_categories & role_cats
        cat_score = len(cat_overlap) / max(len(role_cats), 1)

        # 重み付けスコア: スキルの一致 60% + カテゴリのカバー率 40%
        score = 0.6 * skill_score + 0.4 * cat_score

        if score > 0:
            matches.append(
                RoleMatch(
                    role_name=name,
                    skill_overlap=overlap,
                    category_coverage=cat_score,
                    match_score=round(score, 3),
                )
            )

    matches.sort(key=lambda m: m.match_score, reverse=True)
    return matches
