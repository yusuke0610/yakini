"""
キャリアインテリジェンスパイプラインのオーケストレーター。

GitHub のデータから以下の分析を順次実行します：
  GitHub → リポジトリ → スキル抽出 → タイムライン生成 → 成長分析

オプションの LLM 要約を除き、各ステージは決定論的です。
"""

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

from .github_collector import RepoData, collect_repos
from .position_scorer import PositionScores, calculate_position_scores
from .skill_extractor import ExtractionResult, extract_skills

logger = logging.getLogger(__name__)


@dataclass
class IntelligenceResult:
    """パイプラインの実行結果を保持するデータクラス。"""

    username: str
    repos_analyzed: int
    unique_skills: int
    analyzed_at: str
    languages: Dict[str, int] = field(default_factory=dict)
    position_scores: Optional[PositionScores] = None


async def run_pipeline(
    username: str,
    token: Optional[str] = None,
    include_forks: bool = False,
) -> IntelligenceResult:
    """
    GitHub ユーザーに対してキャリアインテリジェンスパイプラインを実行します。

    パイプラインステージ:
      1. GitHub API からリポジトリを収集
      2. スキルを抽出（決定論的）
      3. スキルタイムラインを構築
      4. 成長速度を分析
    """
    logger.info("%s のインテリジェンスパイプラインを開始します", username)

    # ステージ 1: GitHub データを収集
    repos: List[RepoData] = await collect_repos(
        username,
        token=token,
        include_forks=include_forks,
    )

    # 全リポジトリの言語バイト数を集計
    lang_totals: Dict[str, int] = defaultdict(int)
    for repo in repos:
        for lang, byte_count in repo.languages.items():
            lang_totals[lang] += byte_count

    # ステージ 2: スキルを抽出
    extraction: ExtractionResult = extract_skills(repos)

    # ステージ 3: ポジションスコアを算出
    scores: PositionScores = calculate_position_scores(repos)

    logger.info(
        "パイプライン完了 (%s): 分析リポジトリ数=%d, ユニークスキル数=%d",
        username,
        extraction.repos_analyzed,
        len(extraction.unique_skills),
    )

    return IntelligenceResult(
        username=username,
        repos_analyzed=extraction.repos_analyzed,
        unique_skills=len(extraction.unique_skills),
        analyzed_at=datetime.now().isoformat(),
        languages=dict(lang_totals),
        position_scores=scores,
    )
