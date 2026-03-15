"""
Skill growth velocity analysis.

Detects whether each skill is emerging, stable, or declining
based on yearly usage trends.

Deterministic — no LLM usage.
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
    NEW = "new"  # Only one year of data


@dataclass
class SkillGrowth:
    skill_name: str
    category: str
    trend: GrowthTrend
    velocity: float           # Growth rate (positive = growing)
    yearly_usage: Dict[str, int]
    first_seen: str
    last_seen: str
    total_repos: int


def analyze_growth(
    timelines: List[SkillTimeline],
    current_year: str | None = None,
) -> List[SkillGrowth]:
    """
    Analyze growth velocity for each skill.

    Velocity is calculated as the slope of yearly usage:
      - Positive velocity → emerging
      - Near-zero velocity → stable
      - Negative velocity → declining
    """
    results: List[SkillGrowth] = []

    for timeline in timelines:
        yearly = timeline.yearly_usage
        years = sorted(yearly.keys())

        if len(years) <= 1:
            results.append(SkillGrowth(
                skill_name=timeline.skill_name,
                category=timeline.category,
                trend=GrowthTrend.NEW,
                velocity=0.0,
                yearly_usage=yearly,
                first_seen=timeline.first_seen,
                last_seen=timeline.last_seen,
                total_repos=timeline.usage_frequency,
            ))
            continue

        velocity = _calculate_velocity(yearly)
        trend = _classify_trend(velocity, yearly, current_year)

        results.append(SkillGrowth(
            skill_name=timeline.skill_name,
            category=timeline.category,
            trend=trend,
            velocity=round(velocity, 3),
            yearly_usage=yearly,
            first_seen=timeline.first_seen,
            last_seen=timeline.last_seen,
            total_repos=timeline.usage_frequency,
        ))

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
    Calculate growth velocity using linear regression slope.

    Maps years to sequential indices (0, 1, 2, ...)
    and computes the least-squares slope.
    """
    years = sorted(yearly_usage.keys())
    n = len(years)
    if n < 2:
        return 0.0

    x_vals = list(range(n))
    y_vals = [yearly_usage[y] for y in years]

    x_mean = sum(x_vals) / n
    y_mean = sum(y_vals) / n

    numerator = sum(
        (x - x_mean) * (y - y_mean)
        for x, y in zip(x_vals, y_vals)
    )
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
    Classify the growth trend based on velocity and recency.

    A skill with positive velocity is emerging.
    A skill with negative velocity is declining.
    Near-zero velocity is stable.

    Exception: if the skill hasn't been used recently
    (last 2 years), it's declining regardless of velocity.
    """
    years = sorted(yearly_usage.keys())
    last_year = years[-1] if years else "0"

    # If not used recently, consider declining
    if current_year:
        gap = int(current_year) - int(last_year)
        if gap >= 2:
            return GrowthTrend.DECLINING

    # Threshold for "near zero"
    threshold = 0.3

    if velocity > threshold:
        return GrowthTrend.EMERGING
    elif velocity < -threshold:
        return GrowthTrend.DECLINING
    else:
        return GrowthTrend.STABLE
