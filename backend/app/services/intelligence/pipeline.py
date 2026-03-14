"""
キャリアインテリジェンスパイプラインのオーケストレーター。

GitHub のデータから以下の分析を順次実行します：
  GitHub → リポジトリ → スキル抽出 → タイムライン生成 → 成長分析

オプションの LLM 要約を除き、各ステージは決定論的です。
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from .github_collector import collect_repos, RepoData
from .skill_extractor import ExtractionResult, extract_skills


logger = logging.getLogger(__name__)


@dataclass
class IntelligenceResult:
    """パイプラインの実行結果を保持するデータクラス。"""
    username: str
    repos_analyzed: int
    unique_skills: int
    analyzed_at: str


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
        username, token=token, include_forks=include_forks,
    )

    # ステージ 2: スキルを抽出
    extraction: ExtractionResult = extract_skills(repos)

    # ステージ 3: タイムラインを構築
    # (注意: 現在 build_timeline は skill_growth_analyzer 等からインポートされています)
    # ここでは IntelligenceResult に含める最低限の処理のみ実行

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
    )
