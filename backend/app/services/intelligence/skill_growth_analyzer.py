"""
スキルの成長速度分析。

年次の使用傾向に基づいて、各スキルが台頭中（emerging）、安定（stable）、または衰退中（declining）であるかを検出します。

決定論的 — LLMは使用しません。
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List

from .skill_timeline_builder import SkillTimeline

logger = logging.getLogger(__name__)


class GrowthTrend(str, Enum):
    EMERGING = "emerging"
    STABLE = "stable"
    DECLINING = "declining"
    NEW = "new"  # 1年分のデータのみ


@dataclass
class SkillGrowth:
    skill_name: str
    category: str
    trend: GrowthTrend
    velocity: float  # 成長率（正 = 成長中）
    yearly_usage: Dict[str, int]
    first_seen: str
    last_seen: str
    total_repos: int


def analyze_growth(
    timelines: List[SkillTimeline],
    current_year: str | None = None,
) -> List[SkillGrowth]:
    """
    各スキルの成長速度を分析します。

    速度は年次使用量の傾きとして計算されます：
      - 正の速度 → 台頭中 (emerging)
      - ゼロに近い速度 → 安定 (stable)
      - 負の速度 → 衰退中 (declining)
    """
    results: List[SkillGrowth] = []

    for timeline in timelines:
        yearly = timeline.yearly_usage
        years = sorted(yearly.keys())

        if len(years) <= 1:
            results.append(
                SkillGrowth(
                    skill_name=timeline.skill_name,
                    category=timeline.category,
                    trend=GrowthTrend.NEW,
                    velocity=0.0,
                    yearly_usage=yearly,
                    first_seen=timeline.first_seen,
                    last_seen=timeline.last_seen,
                    total_repos=timeline.usage_frequency,
                )
            )
            continue

        velocity = _calculate_velocity(yearly)
        trend = _classify_trend(velocity, yearly, current_year)

        results.append(
            SkillGrowth(
                skill_name=timeline.skill_name,
                category=timeline.category,
                trend=trend,
                velocity=round(velocity, 3),
                yearly_usage=yearly,
                first_seen=timeline.first_seen,
                last_seen=timeline.last_seen,
                total_repos=timeline.usage_frequency,
            )
        )

    results.sort(key=lambda g: g.velocity, reverse=True)
    logger.info(
        "Growth analysis: %d emerging, %d stable, %d declining, %d new",
        sum(1 for g in results if g.trend == GrowthTrend.EMERGING),
        sum(1 for g in results if g.trend == GrowthTrend.STABLE),
        sum(1 for g in results if g.trend == GrowthTrend.DECLINING),
        sum(1 for g in results if g.trend == GrowthTrend.NEW),
    )
    return results


def _calculate_velocity(yearly_usage: Dict[str, int]) -> float:
    """
    線形回回帰の傾きを使用して成長速度を計算します。

    年を連続したインデックス (0, 1, 2, ...) にマッピングし、
    最小二乗法による傾きを算出します。
    """
    years = sorted(yearly_usage.keys())
    n = len(years)
    if n < 2:
        return 0.0

    x_vals = list(range(n))
    y_vals = [yearly_usage[y] for y in years]

    x_mean = sum(x_vals) / n
    y_mean = sum(y_vals) / n

    numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_vals, y_vals))
    denominator = sum((x - x_mean) ** 2 for x in x_vals)

    if denominator == 0:
        return 0.0

    return numerator / denominator


def _classify_trend(
    velocity: float,
    yearly_usage: Dict[str, int],
    current_year: str | None = None,
) -> GrowthTrend:
    """
    速度と新近性に基づいて成長傾向を分類します。

    正の速度を持つスキルは台頭中 (emerging) です。
    負の速度を持つスキルは衰退中 (declining) です。
    ゼロに近い速度は安定 (stable) です。

    例外：最近（過去2年間）使用されていないスキルは、
    速度に関わらず衰退中 (declining) と見なされます。
    """
    years = sorted(yearly_usage.keys())
    last_year = years[-1] if years else "0"

    # 最近使用されていない場合は衰退中と見なす
    if current_year:
        gap = int(current_year) - int(last_year)
        if gap >= 2:
            return GrowthTrend.DECLINING

    # 「ゼロに近い」と見なす閾値
    threshold = 0.3

    if velocity > threshold:
        return GrowthTrend.EMERGING
    elif velocity < -threshold:
        return GrowthTrend.DECLINING
    else:
        return GrowthTrend.STABLE
