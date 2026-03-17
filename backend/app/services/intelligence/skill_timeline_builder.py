"""
抽出されたスキルデータからスキルタイムラインを構築します。

各スキルが最初にいつ現れ、時間の経過とともに使用状況がどのように変化したかを追跡します。
決定論的 — LLMは使用しません。
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
    first_seen: str        # 年の文字列、例: "2019"
    last_seen: str         # 年の文字列、例: "2024"
    usage_frequency: int   # 合計リポジトリ数
    repositories: List[str]
    yearly_usage: Dict[str, int]  # 年 → リポジトリ数


@dataclass
class YearSnapshot:
    """特定の年にアクティブだったスキル。"""
    year: str
    skills: List[str]
    new_skills: List[str]  # 初めて現れたスキル


def build_timeline(
    extraction: ExtractionResult,
) -> List[SkillTimeline]:
    """
    抽出結果からスキルタイムラインを構築します。

    スキル名を基準にスキルの観測結果をグループ化し、初出/最終確認日、
    および年ごとの使用頻度を計算します。
    """
    # スキルごとに観測結果をグループ化
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

            # pushed_at の年もアクティビティとしてカウント
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
    年ごとのアクティブなスキルを示す年次スナップショットを構築します。

    視覚化に役立ちます。
    """
    # すべての年を収集
    all_years: Set[str] = set()
    for t in timelines:
        all_years.update(t.yearly_usage.keys())

    # スキルごとの初出を追跡
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
    """ISO 8601 形式の日付文字列から年を抽出します。"""
    if not iso_date or len(iso_date) < 4:
        return None
    return iso_date[:4]
