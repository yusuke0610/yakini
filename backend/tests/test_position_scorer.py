"""ポジションスコアのユニットテスト。"""

from app.services.intelligence.github_collector import RepoData
from app.services.intelligence.position_scorer import (
    calculate_position_scores,
)


def _make_repo(
    name="test-repo",
    languages=None,
    topics=None,
    root_files=None,
    detected_frameworks=None,
):
    return RepoData(
        name=name,
        owner="testuser",
        description="",
        languages=languages or {},
        topics=topics or [],
        created_at="2024-01-01T00:00:00Z",
        pushed_at="2024-06-01T00:00:00Z",
        fork=False,
        stargazers_count=0,
        default_branch="main",
        dependencies=[],
        root_files=root_files or [],
        detected_frameworks=detected_frameworks or [],
    )


def test_empty_repos_returns_zero_scores():
    """リポジトリ0件の場合、全スコアが0であること。"""
    result = calculate_position_scores([])
    assert result.backend == 0
    assert result.frontend == 0
    assert result.fullstack == 0
    assert result.sre == 0
    assert result.cloud == 0
    assert len(result.missing_skills) > 0


def test_backend_heavy_repo():
    """Python中心のリポジトリでbackendスコアが高くなること。"""
    repos = [
        _make_repo(
            languages={"Python": 100000},
            topics=["api", "backend", "rest"],
        ),
    ]
    result = calculate_position_scores(repos)
    assert result.backend > 50
    assert result.backend > result.frontend


def test_frontend_heavy_repo():
    """TypeScript/React中心のリポジトリでfrontendスコアが高くなること。"""
    repos = [
        _make_repo(
            languages={"TypeScript": 80000, "CSS": 10000, "HTML": 5000},
            topics=["react", "frontend", "web"],
        ),
    ]
    result = calculate_position_scores(repos)
    assert result.frontend > 50
    assert result.frontend > result.backend


def test_fullstack_balanced():
    """フロント・バック両方のリポジトリがある場合、fullstackスコアが算出されること。"""
    repos = [
        _make_repo(
            name="backend",
            languages={"Python": 50000},
            topics=["api"],
        ),
        _make_repo(
            name="frontend",
            languages={"TypeScript": 50000},
            topics=["react"],
        ),
    ]
    result = calculate_position_scores(repos)
    assert result.fullstack > 0
    # fullstack = min(be, fe) * 0.6 + max(be, fe) * 0.4
    expected = int(
        min(result.backend, result.frontend) * 0.6
        + max(result.backend, result.frontend) * 0.4
    )
    assert result.fullstack == expected


def test_fullstack_one_sided():
    """片方のスコアだけ高い場合、fullstackは低めになること。"""
    repos = [
        _make_repo(languages={"Python": 100000}),
    ]
    result = calculate_position_scores(repos)
    # frontendが0なので fullstack = min(backend, 0) * 0.6 + max * 0.4
    assert result.fullstack <= result.backend


def test_sre_score_with_docker_and_ci():
    """Docker/CI関連ファイルでSREスコアが上がること。"""
    repos = [
        _make_repo(
            languages={"Shell": 30000},
            topics=["docker", "kubernetes", "ci-cd"],
            root_files=["Dockerfile", ".github"],
            detected_frameworks=["Docker", "GitHub Actions"],
        ),
    ]
    result = calculate_position_scores(repos)
    assert result.sre > 30


def test_cloud_score_with_terraform():
    """Terraform/HCL のリポジトリでCloudスコアが上がること。"""
    repos = [
        _make_repo(
            languages={"HCL": 50000},
            topics=["terraform", "aws", "cloud"],
            root_files=["terraform"],
            detected_frameworks=["Terraform"],
        ),
    ]
    result = calculate_position_scores(repos)
    assert result.cloud > 30


def test_missing_skills_detected():
    """バックエンドのみのリポジトリでフロントエンド系スキルが不足として検出されること。"""
    repos = [
        _make_repo(languages={"Python": 100000}, topics=["api"]),
    ]
    result = calculate_position_scores(repos)
    assert any("TypeScript" in s for s in result.missing_skills)
    assert any("React" in s or "Vue" in s for s in result.missing_skills)


def test_no_missing_skills_for_fullstack():
    """全スキルを満たすリポジトリで不足スキルが少ないこと。"""
    repos = [
        _make_repo(
            languages={
                "Python": 30000,
                "TypeScript": 30000,
                "CSS": 5000,
                "HTML": 5000,
                "HCL": 5000,
            },
            topics=["api", "react", "docker", "ci-cd", "aws"],
            root_files=["Dockerfile", ".github", "terraform"],
            detected_frameworks=["Docker", "GitHub Actions", "Terraform"],
        ),
    ]
    result = calculate_position_scores(repos)
    # SQL系がないので完全に0にはならないかもしれない
    assert len(result.missing_skills) <= 2


def test_scores_clamped_to_100():
    """スコアが100を超えないこと。"""
    repos = [
        _make_repo(
            languages={"Python": 1000000},
            topics=[
                "api", "backend", "rest", "graphql",
                "database", "microservices",
            ],
        ),
    ]
    result = calculate_position_scores(repos)
    assert result.backend <= 100
    assert result.frontend <= 100
    assert result.fullstack <= 100
    assert result.sre <= 100
    assert result.cloud <= 100


def test_react_framework_boosts_frontend_score_without_topic_tag():
    """topic タグが無くても React フレームワーク検出で frontend スコアが上がること（Issue #203）。"""
    # トピック無し・ TypeScript のみでは従来 frontend スコアが低い
    repos_without_fw = [
        _make_repo(languages={"TypeScript": 100000}),
    ]
    baseline = calculate_position_scores(repos_without_fw).frontend

    # 依存関係から React を検出したケース
    repos_with_fw = [
        _make_repo(
            languages={"TypeScript": 100000},
            detected_frameworks=["React", "Next.js"],
        ),
    ]
    boosted = calculate_position_scores(repos_with_fw).frontend
    assert boosted > baseline


def test_react_framework_satisfies_react_or_vue_requirement():
    """React フレームワーク検出で missing_skills から `React or Vue` が消えること（Issue #203）。"""
    repos = [
        _make_repo(
            languages={"TypeScript": 80000, "Python": 20000, "CSS": 5000, "HTML": 5000},
            detected_frameworks=["React", "FastAPI"],
        ),
    ]
    result = calculate_position_scores(repos)
    assert not any("React or Vue" in s for s in result.missing_skills)


def test_fastapi_framework_satisfies_rest_api_requirement():
    """FastAPI 検出で REST API 設計要件が満たされること。"""
    repos = [
        _make_repo(
            languages={"Python": 100000},
            detected_frameworks=["FastAPI"],
        ),
    ]
    result = calculate_position_scores(repos)
    assert not any("REST API設計" in s for s in result.missing_skills)
