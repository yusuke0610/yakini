"""
スキルアクティビティ分析。

GitHub のコミット履歴を収集し、pandas を使用してスキルごとの
アクティビティ（月次または年次）を集計します。
"""

import logging
from typing import Dict, List, Literal, Optional

import pandas as pd
from github import Github
from github.GithubException import GithubException

from .github_collector import collect_repos
from .skill_extractor import _extract_from_repo

logger = logging.getLogger(__name__)


async def get_skill_activity(
    username: str,
    token: Optional[str] = None,
    interval: Literal["month", "year"] = "month",
    max_repos: int = 10,
    max_commits_per_repo: int = 1000,
) -> List[Dict]:
    """
    コミット履歴を取得し、スキルごとのアクティビティを集計します。

    スキル名とそのアクティビティタイムラインのリストを返します。
    """
    # 1. リポジトリを収集（既存のコレクターを使用してスキルメタデータを取得）
    # 速度優先のため max_pages を制限
    repos_data = await collect_repos(
        username=username,
        token=token,
        include_forks=False,
        max_pages=2,
    )

    # pushed_at でソートして上位 N 件に制限、または最初の N 件を取得
    repos_data = sorted(
        repos_data,
        key=lambda r: r.pushed_at,
        reverse=True
    )[:max_repos]

    if not repos_data:
        return []

    # 2. コミット取得用に GitHub クライアントを初期化
    g = Github(token) if token else Github()

    all_commit_data = []

    for repo_info in repos_data:
        try:
            # このリポジトリのスキルを抽出
            extracted_skills = _extract_from_repo(repo_info)
            if not extracted_skills:
                continue

            # 言語バイト比率による重み付けを計算
            total_bytes = sum(repo_info.languages.values()) or 1
            # 主要言語の重みを算出（フレームワークに継承させるため）
            max_lang_weight = (
                max(repo_info.languages.values()) / total_bytes
                if repo_info.languages else 0.1
            )
            skill_weights: Dict[str, float] = {}
            for extracted in extracted_skills:
                if extracted.language_bytes > 0:
                    # 言語系スキル: バイト比率を重みとして使用
                    skill_weights[extracted.skill_name] = (
                        extracted.language_bytes / total_bytes
                    )
                elif extracted.source == "dependency":
                    # フレームワーク系スキル: 主要言語の重みを継承
                    skill_weights[extracted.skill_name] = max_lang_weight
                else:
                    # インフラ系スキル (Docker, CI等): 固定の小さい重み
                    skill_weights[extracted.skill_name] = 0.1

            repo = g.get_repo(f"{repo_info.owner}/{repo_info.name}")

            # コミットを取得
            commits = repo.get_commits()
            count = 0
            for commit in commits:
                if count >= max_commits_per_repo:
                    break

                # コミット日時を取得
                commit_date = commit.commit.author.date
                if commit_date:
                    for skill, weight in skill_weights.items():
                        all_commit_data.append({
                            "date": commit_date,
                            "skill": skill,
                            "weight": weight,
                        })

                count += 1

        except GithubException as e:
            logger.warning(
                "%s/%s のコミット取得に失敗しました: %s",
                repo_info.owner, repo_info.name, e
            )
            continue
        except Exception as e:
            logger.exception(
                "%s のコミット取得中に予期せぬエラーが発生しました: %s",
                repo_info.name, e
            )
            continue

    if not all_commit_data:
        return []

    # 3. pandas を使用して集計
    df = pd.DataFrame(all_commit_data)
    df['date'] = pd.to_datetime(df['date'])

    # 頻度を設定
    freq = "ME" if interval == "month" else "YE"

    # スキルと期間でグループ化
    # タイムシリーズを正しく扱うために resample を使用
    results = []

    unique_skills = df['skill'].unique()
    for skill in unique_skills:
        skill_df = df[df['skill'] == skill].copy()

        # 期間でグループ化（重みの合計でアクティビティを算出）
        grouped = (
            skill_df.set_index('date')['weight']
            .resample(freq).sum().reset_index(name='activity')
        )

        # 期間文字列をフォーマット
        if interval == "month":
            grouped['period'] = grouped['date'].dt.strftime('%Y-%m')
        else:
            grouped['period'] = grouped['date'].dt.strftime('%Y')

        timeline = grouped[['period', 'activity']].to_dict('records')

        # 折れ線グラフの場合、活動期間の間のゼロは維持するのが望ましい
        # 必要に応じて先頭・末尾のゼロを除去することも検討可能

        results.append({
            "skill": skill,
            "timeline": timeline
        })

    return results
