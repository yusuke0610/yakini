"""
Builds skill timelines from extracted skill data.

Tracks when each skill first appeared and how usage evolved over time.
Deterministic — no LLM usage.
"""

import logging
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Set

from .skill_extractor import ExtractedSkill, ExtractionResult

logger = logging.getLogger(__name__)


@dataclass
class SkillTimeline:
    skill_name: str
    category: str
    first_seen: str        # Year string, e.g. "2019"
    last_seen: str         # Year string, e.g. "2024"
    usage_frequency: int   # Total repo count
    repositories: List[str]
    yearly_usage: Dict[str, int]  # year → repo count


@dataclass
class YearSnapshot:
    """Skills active in a given year."""
    year: str
    skills: List[str]
    new_skills: List[str]  # Skills that appeared for the first time


def build_timeline(
    extraction: ExtractionResult,
) -> List[SkillTimeline]:
    """
    Build a skill timeline from extraction results.

    Groups skill observations by skill name, calculates first/last seen,
    and yearly usage frequency.
    """
    # Group observations by skill
    skill_data: Dict[str, List[ExtractedSkill]] = defaultdict(list)
    for obs in extraction.skills:
        skill_data[obs.skill_name].append(obs)

    timelines: List[SkillTimeline] = []

    for skill_name, observations in skill_data.items():
        yearly: Dict[str, Set[str]] = defaultdict(set)
        all_repos: Set[str] = set()
        category = observations[0].category

        for obs in observations:
            year = _extract_year(obs.repo_created_at)
            if year:
                yearly[year].add(obs.repo_name)
            all_repos.add(obs.repo_name)

            # Also count pushed_at year as activity
            push_year = _extract_year(obs.repo_pushed_at)
            if push_year and push_year != year:
                yearly[push_year].add(obs.repo_name)

        years = sorted(yearly.keys())
        if not years:
            continue

        yearly_usage = {y: len(repos) for y, repos in sorted(yearly.items())}

        timelines.append(SkillTimeline(
            skill_name=skill_name,
            category=category,
            first_seen=years[0],
            last_seen=years[-1],
            usage_frequency=len(all_repos),
            repositories=sorted(all_repos),
            yearly_usage=yearly_usage,
        ))

    timelines.sort(key=lambda t: (t.first_seen, -t.usage_frequency))
    logger.info("Built timeline for %d skills", len(timelines))
    return timelines


def build_year_snapshots(
    timelines: List[SkillTimeline],
) -> List[YearSnapshot]:
    """
    Build year-by-year snapshots showing active skills per year.

    Useful for visualization.
    """
    # Collect all years
    all_years: Set[str] = set()
    for t in timelines:
        all_years.update(t.yearly_usage.keys())

    # Track first-seen per skill
    first_seen_map: Dict[str, str] = {
        t.skill_name: t.first_seen for t in timelines
    }

    snapshots: List[YearSnapshot] = []
    for year in sorted(all_years):
        active = [
            t.skill_name for t in timelines
            if year in t.yearly_usage
        ]
        new = [
            s for s in active if first_seen_map.get(s) == year
        ]
        snapshots.append(YearSnapshot(
            year=year,
            skills=sorted(active),
            new_skills=sorted(new),
        ))

    return snapshots


def _extract_year(iso_date: str) -> str | None:
    """Extract year from ISO 8601 date string."""
    if not iso_date or len(iso_date) < 4:
        return None
    return iso_date[:4]
