"""
エンジニアポジションスコアの算出。

GitHubリポジトリデータから5軸（Backend / Frontend / Fullstack / SRE / Cloud）の
適性スコアを0-100で算出する。

スキル分類辞書（言語→スキル、トピック→スキル、フレームワーク→スキル）は
``skill_taxonomy/ownership_map.py`` に集約されており、本モジュールは
スコア計算ロジックと不足スキル判定の関数のみを持つ。
"""

import json
import logging
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Set

from .github_collector import RepoData
from .skill_taxonomy import (
    FILE_SKILL_MAP,
    FRAMEWORK_SKILL_MAP,
    FRAMEWORK_TO_TOPICS,
    LANG_SKILL_MAP,
    LANG_SKILL_THRESHOLD,
    TOPIC_SKILL_MAP,
)

logger = logging.getLogger(__name__)

_WEIGHTS_PATH = os.path.join(os.path.dirname(__file__), "position_weights.json")

with open(_WEIGHTS_PATH, encoding="utf-8") as _f:
    _WEIGHTS: Dict[str, Any] = json.load(_f)


@dataclass
class PositionScores:
    """5軸のポジションスコアと不足スキル情報。"""

    backend: int = 0
    frontend: int = 0
    fullstack: int = 0
    sre: int = 0
    cloud: int = 0
    missing_skills: List[str] = field(default_factory=list)


def calculate_position_scores(repos: List[RepoData]) -> PositionScores:
    """
    リポジトリデータから各ポジションのスコアを算出する。

    算出ロジック:
      1. 全リポジトリの言語バイト数を集計し、言語比率を計算
      2. 全リポジトリのトピック・ルートファイルを収集
      3. 各ポジション（backend/frontend/sre/cloud）の重み定義に基づきスコア算出
      4. fullstack = min(backend, frontend) * 0.6 + max(backend, frontend) * 0.4
      5. フルスタック要件との差分から不足スキルを特定
    """
    if not repos:
        return PositionScores(
            missing_skills=_get_all_requirements(),
        )

    # 全リポジトリの言語バイト数を集計
    lang_totals: Dict[str, int] = {}
    for repo in repos:
        for lang, bytes_count in repo.languages.items():
            lang_totals[lang] = lang_totals.get(lang, 0) + bytes_count

    total_bytes = sum(lang_totals.values()) or 1
    lang_ratios = {lang: b / total_bytes for lang, b in lang_totals.items()}

    # 全リポジトリのトピック・ルートファイルを収集
    all_topics: Set[str] = set()
    all_files: Set[str] = set()
    all_frameworks: Set[str] = set()
    for repo in repos:
        all_topics.update(t.lower() for t in repo.topics)
        all_files.update(repo.root_files)
        all_frameworks.update(repo.detected_frameworks)
        all_frameworks.update(repo.detected_devtools)
        all_frameworks.update(repo.detected_infras)


    # 検出フレームワークを等価なトピックに展開してスコア算出に反映させる
    # （リポジトリに topic タグが無くても依存関係から推定できるようにする）
    for fw in all_frameworks:
        all_topics.update(FRAMEWORK_TO_TOPICS.get(fw, ()))

    # 各ポジションのスコア算出
    backend = _calc_axis_score("backend", lang_ratios, all_topics, all_files)
    frontend = _calc_axis_score("frontend", lang_ratios, all_topics, all_files)
    sre = _calc_axis_score("sre", lang_ratios, all_topics, all_files)
    cloud = _calc_axis_score("cloud", lang_ratios, all_topics, all_files)

    # Fullstack: 弱い方に引っ張られる計算
    fs_min = min(backend, frontend)
    fs_max = max(backend, frontend)
    fullstack = int(fs_min * 0.6 + fs_max * 0.4)

    # 不足スキル分析
    detected_skills = _detect_owned_skills(
        lang_ratios, all_topics, all_files, all_frameworks,
    )
    missing = _find_missing_skills(detected_skills)

    return PositionScores(
        backend=backend,
        frontend=frontend,
        fullstack=fullstack,
        sre=sre,
        cloud=cloud,
        missing_skills=missing,
    )


def _calc_axis_score(
    axis: str,
    lang_ratios: Dict[str, float],
    topics: Set[str],
    files: Set[str],
) -> int:
    """
    単一ポジション軸のスコアを算出する。

    言語比率 × 重み（最大70点）+ トピックマッチ（最大20点）+ ファイルマッチ（最大10点）
    → 0-100 にクランプ。
    """
    cfg = _WEIGHTS.get(axis, {})

    # 言語スコア（最大70点）
    lang_weights = cfg.get("languages", {})
    lang_score = 0.0
    for lang, weight in lang_weights.items():
        ratio = lang_ratios.get(lang, 0.0)
        lang_score += ratio * weight
    # 言語スコアを0-70に正規化
    max_lang_weight = max(lang_weights.values()) if lang_weights else 1
    lang_score = min(lang_score / max_lang_weight * 70, 70)

    # トピックスコア（最大20点）
    cfg_topics = cfg.get("topics", [])
    if cfg_topics:
        matched_topics = sum(1 for t in cfg_topics if t in topics)
        topic_score = min(matched_topics / len(cfg_topics) * 60, 20)
    else:
        topic_score = 0.0

    # ファイルスコア（最大10点）
    cfg_files = cfg.get("files", [])
    if cfg_files:
        matched_files = sum(1 for f in cfg_files if f in files)
        file_score = min(matched_files / len(cfg_files) * 30, 10)
    else:
        file_score = 0.0

    raw = lang_score + topic_score + file_score
    return min(int(raw), 100)


def _detect_owned_skills(
    lang_ratios: Dict[str, float],
    topics: Set[str],
    files: Set[str],
    frameworks: Set[str],
) -> Set[str]:
    """ユーザーが保有しているスキルを特定する。"""
    owned: Set[str] = set()

    for lang, skill in LANG_SKILL_MAP.items():
        if lang_ratios.get(lang, 0) >= LANG_SKILL_THRESHOLD:
            owned.add(skill)

    for topic, skill in TOPIC_SKILL_MAP.items():
        if topic in topics:
            owned.add(skill)

    for fname, skill in FILE_SKILL_MAP.items():
        if fname in files:
            owned.add(skill)

    for fw, skill in FRAMEWORK_SKILL_MAP.items():
        if fw in frameworks:
            owned.add(skill)

    return owned


# 要件名 → 必要スキル集合（いずれか一つ満たせば OK）
# 中身は ``position_weights.json`` の ``requirement_skill_map`` から構築する。
_REQUIREMENT_TO_OWNED_SKILLS: Dict[str, Set[str]] = {
    req: set(skills)
    for req, skills in _WEIGHTS.get("requirement_skill_map", {}).items()
}


def _find_missing_skills(owned: Set[str]) -> List[str]:
    """フルスタック要件と保有スキルの差分を算出する。"""
    requirements = _WEIGHTS.get("fullstack_requirements", {})
    missing: List[str] = []

    for req_list in requirements.values():
        for req in req_list:
            needed = _REQUIREMENT_TO_OWNED_SKILLS.get(req, set())
            if needed and not (owned & needed):
                missing.append(req)

    return missing


def _get_all_requirements() -> List[str]:
    """全フルスタック要件をリストで返す（リポジトリ0件時用）。"""
    requirements = _WEIGHTS.get("fullstack_requirements", {})
    all_reqs: List[str] = []
    for req_list in requirements.values():
        all_reqs.extend(req_list)
    return all_reqs
