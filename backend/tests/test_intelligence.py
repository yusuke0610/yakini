"""
Unit tests for the career intelligence services.

Tests cover deterministic modules only (no GitHub API calls).
"""

from fastapi.testclient import TestClient

from conftest import auth_header
from app.services.intelligence.github_collector import RepoData
from app.services.intelligence.pipeline import IntelligenceResult
from app.services.intelligence.response_mapper import map_pipeline_result
from app.services.intelligence.skill_extractor import extract_skills
from app.services.intelligence.skill_timeline_builder import (
    build_timeline,
    build_year_snapshots,
)
from app.services.intelligence.skill_growth_analyzer import (
    GrowthTrend,
    analyze_growth,
)
from app.services.intelligence.career_paths import (
    match_skills_to_roles,
)
from app.services.intelligence.career_predictor import predict_career
from app.services.intelligence.career_simulator import simulate_careers
from app.services.intelligence.confidence_scorer import score_path


# ── Test Fixtures ───────────────────────────────────────────────────────

def _make_repo(
    name="my-repo",
    languages=None,
    topics=None,
    description="",
    created_at="2022-01-01T00:00:00Z",
    pushed_at="2023-06-01T00:00:00Z",
    dependencies=None,
    root_files=None,
    detected_frameworks=None,
):
    return RepoData(
        name=name,
        owner="testuser",
        description=description,
        languages=languages or {},
        topics=topics or [],
        created_at=created_at,
        pushed_at=pushed_at,
        fork=False,
        stargazers_count=0,
        default_branch="main",
        dependencies=dependencies or [],
        root_files=root_files or [],
        detected_frameworks=detected_frameworks or [],
    )


SAMPLE_REPOS = [
    _make_repo(
        name="web-api",
        languages={"Python": 50000, "Dockerfile": 500},
        topics=["fastapi", "docker", "postgresql"],
        description="FastAPI backend with PostgreSQL",
        created_at="2021-03-01T00:00:00Z",
        pushed_at="2024-01-15T00:00:00Z",
    ),
    _make_repo(
        name="infra",
        languages={"HCL": 30000, "Shell": 2000},
        topics=["terraform", "gcp", "kubernetes"],
        description="GCP infrastructure with Terraform",
        created_at="2023-01-01T00:00:00Z",
        pushed_at="2024-06-01T00:00:00Z",
    ),
    _make_repo(
        name="frontend",
        languages={"TypeScript": 40000, "JavaScript": 5000},
        topics=["react", "nextjs"],
        description="React frontend",
        created_at="2022-06-01T00:00:00Z",
        pushed_at="2023-12-01T00:00:00Z",
    ),
    _make_repo(
        name="old-java",
        languages={"Java": 80000},
        topics=["spring-boot"],
        description="Legacy Spring Boot service",
        created_at="2019-01-01T00:00:00Z",
        pushed_at="2020-06-01T00:00:00Z",
    ),
    _make_repo(
        name="scripts",
        languages={"Python": 3000},
        topics=[],
        description="Utility scripts",
        created_at="2020-01-01T00:00:00Z",
        pushed_at="2020-12-01T00:00:00Z",
    ),
]


# ── Skill Extractor ─────────────────────────────────────────────────────

class TestSkillExtractor:

    def test_extracts_from_languages(self):
        repos = [_make_repo(languages={"Python": 10000, "Go": 5000})]
        result = extract_skills(repos)
        names = {s.skill_name for s in result.skills}
        assert "Python" in names
        assert "Go" in names

    def test_extracts_from_topics(self):
        repos = [_make_repo(topics=["react", "docker", "postgresql"])]
        result = extract_skills(repos)
        names = {s.skill_name for s in result.skills}
        assert "React" in names
        assert "Docker" in names
        assert "PostgreSQL" in names

    def test_extracts_from_description(self):
        repos = [_make_repo(description="Built with FastAPI and Redis")]
        result = extract_skills(repos)
        names = {s.skill_name for s in result.skills}
        assert "FastAPI" in names
        assert "Redis" in names

    def test_deduplicates_within_repo(self):
        """Same skill from language + topic should appear once per repo."""
        repos = [_make_repo(
            languages={"Python": 10000},
            topics=["fastapi"],
            description="A FastAPI project",
        )]
        result = extract_skills(repos)
        python_count = sum(
            1 for s in result.skills
            if s.skill_name == "Python" and s.repo_name == "my-repo"
        )
        assert python_count == 1

    def test_hcl_maps_to_terraform(self):
        repos = [_make_repo(languages={"HCL": 5000})]
        result = extract_skills(repos)
        names = {s.skill_name for s in result.skills}
        assert "Terraform" in names

    def test_empty_repos(self):
        result = extract_skills([])
        assert result.skills == []
        assert result.repos_analyzed == 0

    def test_unique_skills_count(self):
        result = extract_skills(SAMPLE_REPOS)
        assert len(result.unique_skills) > 5
        assert result.repos_analyzed == 5

    def test_source_tracking(self):
        repos = [_make_repo(
            languages={"Python": 10000},
            topics=["docker"],
        )]
        result = extract_skills(repos)
        sources = {s.source for s in result.skills}
        assert "language" in sources
        assert "topic" in sources

    def test_extracts_from_dependencies(self):
        repos = [_make_repo(
            dependencies=["fastapi", "sqlalchemy", "uvicorn"],
        )]
        result = extract_skills(repos)
        names = {s.skill_name for s in result.skills}
        assert "FastAPI" in names
        assert "SQLAlchemy" in names

    def test_extracts_from_detected_frameworks(self):
        repos = [_make_repo(
            detected_frameworks=["Docker", "GitHub Actions", "Terraform"],
        )]
        result = extract_skills(repos)
        names = {s.skill_name for s in result.skills}
        assert "Docker" in names
        assert "GitHub Actions" in names
        assert "Terraform" in names

    def test_dependency_source_label(self):
        repos = [_make_repo(dependencies=["fastapi"])]
        result = extract_skills(repos)
        sources = {s.source for s in result.skills}
        assert "dependency" in sources

    def test_root_file_source_label(self):
        repos = [_make_repo(detected_frameworks=["Docker"])]
        result = extract_skills(repos)
        sources = {s.source for s in result.skills}
        assert "root_file" in sources

    def test_dedup_dependency_and_topic(self):
        """Same skill from topic + dependency should appear once."""
        repos = [_make_repo(
            topics=["fastapi"],
            dependencies=["fastapi"],
        )]
        result = extract_skills(repos)
        fastapi_count = sum(
            1 for s in result.skills if s.skill_name == "FastAPI"
        )
        assert fastapi_count == 1

    def test_dedup_root_file_and_language(self):
        """Docker from language + root_file should appear once."""
        repos = [_make_repo(
            languages={"Dockerfile": 500},
            detected_frameworks=["Docker"],
        )]
        result = extract_skills(repos)
        docker_count = sum(
            1 for s in result.skills if s.skill_name == "Docker"
        )
        assert docker_count == 1

    def test_full_repo_with_all_sources(self):
        """A realistic repo should produce rich skill set."""
        repos = [_make_repo(
            name="fullstack-app",
            languages={"Python": 50000, "Dockerfile": 500},
            topics=["fastapi", "postgresql"],
            description="Backend API",
            dependencies=["fastapi", "sqlalchemy", "boto3"],
            root_files=["Dockerfile", ".github", "terraform"],
            detected_frameworks=["Docker", "GitHub Actions", "Terraform"],
        )]
        result = extract_skills(repos)
        names = {s.skill_name for s in result.skills}
        assert "Python" in names
        assert "FastAPI" in names
        assert "PostgreSQL" in names
        assert "Docker" in names
        assert "GitHub Actions" in names
        assert "Terraform" in names
        assert "SQLAlchemy" in names
        assert "AWS" in names  # from boto3 dependency


# ── Root File Detection ─────────────────────────────────────────────────

class TestRootFileDetection:

    def test_dockerfile_detected(self):
        from app.services.intelligence.github_collector import (
            _detect_from_root_files,
        )
        result = _detect_from_root_files(["Dockerfile"])
        assert "Docker" in result

    def test_docker_compose_detected(self):
        from app.services.intelligence.github_collector import (
            _detect_from_root_files,
        )
        result = _detect_from_root_files(["docker-compose.yml"])
        assert "Docker Compose" in result

    def test_github_actions_detected(self):
        from app.services.intelligence.github_collector import (
            _detect_from_root_files,
        )
        result = _detect_from_root_files([".github"])
        assert "GitHub Actions" in result

    def test_terraform_detected(self):
        from app.services.intelligence.github_collector import (
            _detect_from_root_files,
        )
        result = _detect_from_root_files(["terraform"])
        assert "Terraform" in result

    def test_makefile_detected(self):
        from app.services.intelligence.github_collector import (
            _detect_from_root_files,
        )
        result = _detect_from_root_files(["Makefile"])
        assert "Build Automation" in result

    def test_no_duplicates(self):
        from app.services.intelligence.github_collector import (
            _detect_from_root_files,
        )
        result = _detect_from_root_files([
            "terraform", ".terraform",
        ])
        assert result.count("Terraform") == 1


# ── Dependency Parsing ──────────────────────────────────────────────────

class TestDependencyParsing:

    def test_parse_requirements_txt(self):
        from app.services.intelligence.github_collector import (
            _parse_requirements_txt,
        )
        content = "fastapi>=0.100\nuvicorn\nsqlalchemy==2.0\n# comment\n"
        result = _parse_requirements_txt(content)
        assert "fastapi" in result
        assert "uvicorn" in result
        assert "sqlalchemy" in result

    def test_parse_requirements_txt_with_extras(self):
        from app.services.intelligence.github_collector import (
            _parse_requirements_txt,
        )
        content = "uvicorn[standard]>=0.20\nboto3\n"
        result = _parse_requirements_txt(content)
        assert "uvicorn" in result
        assert "boto3" in result

    def test_parse_package_json(self):
        from app.services.intelligence.github_collector import (
            _parse_package_json,
        )
        content = '{"dependencies":{"react":"^18","next":"^14"}}'
        result = _parse_package_json(content)
        assert "react" in result
        assert "next" in result

    def test_parse_package_json_with_dev_deps(self):
        from app.services.intelligence.github_collector import (
            _parse_package_json,
        )
        content = (
            '{"dependencies":{"react":"^18"},'
            '"devDependencies":{"jest":"^29"}}'
        )
        result = _parse_package_json(content)
        assert "react" in result
        assert "jest" in result

    def test_parse_package_json_invalid(self):
        from app.services.intelligence.github_collector import (
            _parse_package_json,
        )
        result = _parse_package_json("not json")
        assert result == []

    def test_parse_pom_xml(self):
        from app.services.intelligence.github_collector import (
            _parse_pom_xml,
        )
        content = (
            "<project><dependencies><dependency>"
            "<artifactId>spring-boot-starter-web</artifactId>"
            "</dependency></dependencies></project>"
        )
        result = _parse_pom_xml(content)
        assert "spring-boot-starter-web" in result

    def test_parse_go_mod(self):
        from app.services.intelligence.github_collector import (
            _parse_go_mod,
        )
        content = (
            "module example.com/app\n\nrequire (\n"
            "\tgithub.com/gin-gonic/gin v1.9\n)\n"
        )
        result = _parse_go_mod(content)
        assert "github.com/gin-gonic/gin" in result

    def test_dependency_to_framework_mapping(self):
        from app.services.intelligence.github_collector import (
            DEPENDENCY_TO_FRAMEWORK,
        )
        assert DEPENDENCY_TO_FRAMEWORK["fastapi"] == "FastAPI"
        assert DEPENDENCY_TO_FRAMEWORK["react"] == "React"
        assert DEPENDENCY_TO_FRAMEWORK["torch"] == "PyTorch"
        assert DEPENDENCY_TO_FRAMEWORK["boto3"] == "AWS"


# ── Skill Timeline ──────────────────────────────────────────────────────

class TestSkillTimeline:

    def _build(self):
        extraction = extract_skills(SAMPLE_REPOS)
        return build_timeline(extraction)

    def test_builds_timeline_entries(self):
        timelines = self._build()
        assert len(timelines) > 0
        names = {t.skill_name for t in timelines}
        assert "Python" in names

    def test_first_seen_last_seen(self):
        timelines = self._build()
        python = next(t for t in timelines if t.skill_name == "Python")
        assert python.first_seen <= python.last_seen

    def test_yearly_usage_populated(self):
        timelines = self._build()
        python = next(t for t in timelines if t.skill_name == "Python")
        assert len(python.yearly_usage) > 0
        for year, count in python.yearly_usage.items():
            assert len(year) == 4
            assert count > 0

    def test_repositories_listed(self):
        timelines = self._build()
        python = next(t for t in timelines if t.skill_name == "Python")
        assert "web-api" in python.repositories
        assert "scripts" in python.repositories

    def test_java_timeline(self):
        timelines = self._build()
        java = next(t for t in timelines if t.skill_name == "Java")
        assert java.first_seen == "2019"

    def test_year_snapshots(self):
        timelines = self._build()
        snapshots = build_year_snapshots(timelines)
        assert len(snapshots) > 0
        years = [s.year for s in snapshots]
        assert years == sorted(years)

    def test_snapshot_new_skills(self):
        timelines = self._build()
        snapshots = build_year_snapshots(timelines)
        # Each skill should appear as new in exactly one year
        all_new = []
        for s in snapshots:
            all_new.extend(s.new_skills)
        assert len(all_new) == len(set(all_new))


# ── Skill Growth Analyzer ──────────────────────────────────────────────

class TestSkillGrowthAnalyzer:

    def _analyze(self, current_year="2024"):
        extraction = extract_skills(SAMPLE_REPOS)
        timelines = build_timeline(extraction)
        return analyze_growth(timelines, current_year=current_year)

    def test_returns_all_skills(self):
        growth = self._analyze()
        assert len(growth) > 0
        names = {g.skill_name for g in growth}
        assert "Python" in names

    def test_trend_classification(self):
        growth = self._analyze()
        trends = {g.trend for g in growth}
        # Should have at least two different trends
        assert len(trends) >= 2

    def test_velocity_is_float(self):
        growth = self._analyze()
        for g in growth:
            assert isinstance(g.velocity, float)

    def test_old_unused_skill_declining(self):
        """Java used only in 2019-2020 should be declining by 2024."""
        growth = self._analyze(current_year="2024")
        java = next(
            (g for g in growth if g.skill_name == "Java"),
            None,
        )
        if java:
            assert java.trend == GrowthTrend.DECLINING

    def test_single_year_skill_is_new(self):
        """A skill seen only in one year should be classified as NEW."""
        repos = [_make_repo(
            languages={"Rust": 5000},
            created_at="2024-01-01T00:00:00Z",
            pushed_at="2024-01-01T00:00:00Z",
        )]
        extraction = extract_skills(repos)
        timelines = build_timeline(extraction)
        growth = analyze_growth(timelines)
        rust = next(g for g in growth if g.skill_name == "Rust")
        assert rust.trend == GrowthTrend.NEW


# ── Career Paths Matching ──────────────────────────────────────────────

class TestCareerPathsMatching:

    def test_backend_skills_match_backend_engineer(self):
        skills = {"Python", "FastAPI", "PostgreSQL"}
        categories = {"language", "backend_framework", "database"}
        matches = match_skills_to_roles(skills, categories)
        role_names = [m.role_name for m in matches]
        assert "Backend Engineer" in role_names

    def test_frontend_skills_match_frontend_engineer(self):
        skills = {"TypeScript", "React", "Next.js"}
        categories = {"language", "frontend_framework"}
        matches = match_skills_to_roles(skills, categories)
        role_names = [m.role_name for m in matches]
        assert "Frontend Engineer" in role_names

    def test_infra_skills_match_devops(self):
        skills = {"Docker", "Kubernetes", "Terraform", "GitHub Actions"}
        categories = {"infrastructure", "cicd"}
        matches = match_skills_to_roles(skills, categories)
        role_names = [m.role_name for m in matches]
        assert "DevOps Engineer" in role_names

    def test_empty_skills_no_match(self):
        matches = match_skills_to_roles(set(), set())
        assert matches == []

    def test_match_score_between_0_and_1(self):
        skills = {"Python", "FastAPI", "Docker", "AWS"}
        categories = {
            "language",
            "backend_framework",
            "infrastructure",
            "cloud"
        }
        matches = match_skills_to_roles(skills, categories)
        for m in matches:
            assert 0 < m.match_score <= 1.0

    def test_matches_sorted_by_score(self):
        skills = {"Python", "FastAPI", "Docker", "TypeScript", "React"}
        categories = {
            "language",
            "backend_framework",
            "infrastructure",
            "frontend_framework",
        }
        matches = match_skills_to_roles(skills, categories)
        scores = [m.match_score for m in matches]
        assert scores == sorted(scores, reverse=True)


# ── Career Predictor ────────────────────────────────────────────────────

class TestCareerPredictor:

    def _predict(self):
        extraction = extract_skills(SAMPLE_REPOS)
        timelines = build_timeline(extraction)
        growth = analyze_growth(timelines, current_year="2024")
        return predict_career(timelines, growth)

    def test_has_current_role(self):
        prediction = self._predict()
        assert prediction.current_role.role_name
        assert prediction.current_role.confidence >= 0

    def test_has_next_roles(self):
        prediction = self._predict()
        assert len(prediction.next_roles) > 0

    def test_confidence_range(self):
        prediction = self._predict()
        for role in [prediction.current_role] + prediction.next_roles:
            assert 0 <= role.confidence <= 1.0

    def test_skill_summary_populated(self):
        prediction = self._predict()
        assert len(prediction.skill_summary) > 0
        total_skills = sum(
            len(skills) for skills in prediction.skill_summary.values()
        )
        assert total_skills > 0

    def test_empty_input(self):
        prediction = predict_career([], [])
        assert prediction.current_role.role_name == "Developer"
        assert prediction.current_role.confidence == 0.0


# ── Career Simulator ────────────────────────────────────────────────────

class TestCareerSimulator:

    def _simulate(self):
        extraction = extract_skills(SAMPLE_REPOS)
        timelines = build_timeline(extraction)
        growth = analyze_growth(timelines, current_year="2024")
        prediction = predict_career(timelines, growth)
        return simulate_careers(prediction, timelines, growth)

    def test_returns_paths(self):
        simulation = self._simulate()
        assert len(simulation.paths) > 0

    def test_paths_start_with_current_role(self):
        simulation = self._simulate()
        for path in simulation.paths:
            assert path.path[0] == simulation.current_role

    def test_path_confidence_range(self):
        simulation = self._simulate()
        for path in simulation.paths:
            assert 0 <= path.confidence <= 1.0

    def test_path_length_reasonable(self):
        simulation = self._simulate()
        for path in simulation.paths:
            assert 2 <= len(path.path) <= 5

    def test_paths_sorted_by_confidence(self):
        simulation = self._simulate()
        confidences = [p.confidence for p in simulation.paths]
        assert confidences == sorted(confidences, reverse=True)

    def test_no_cycles_in_paths(self):
        simulation = self._simulate()
        for path in simulation.paths:
            assert len(path.path) == len(set(path.path))

    def test_description_populated(self):
        simulation = self._simulate()
        for path in simulation.paths:
            assert len(path.description) > 0


# ── Confidence Scorer ───────────────────────────────────────────────────

class TestConfidenceScorer:

    def test_score_range(self):
        skills = {"Python", "FastAPI", "Docker"}
        categories = {"language", "backend_framework", "infrastructure"}
        score = score_path(
            ["Backend Engineer", "Platform Engineer"],
            skills, categories, {},
        )
        assert 0 <= score <= 1.0

    def test_longer_path_lower_confidence(self):
        skills = {"Python", "FastAPI", "Docker", "AWS", "Terraform"}
        categories = {
            "language",
            "backend_framework",
            "infrastructure",
            "cloud"
            }
        short = score_path(
            ["Backend Engineer", "Platform Engineer"],
            skills, categories, {},
        )
        long = score_path(
            [
                "Backend Engineer",
                "Platform Engineer",
                "Cloud Architect",
                "CTO"],
            skills, categories, {},
        )
        assert short >= long

    def test_empty_path(self):
        assert score_path([], set(), set(), {}) == 0.0

    def test_single_role_path(self):
        assert (
            score_path(
                ["Backend Engineer"],
                {"Python"},
                {"language"},
                {},
            ) == 0.0
        )

    def test_better_skill_match_higher_score(self):
        categories = {
            "language",
            "backend_framework",
            "infrastructure",
            "cloud",
        }
        path = ["Backend Engineer", "Platform Engineer"]
        low = score_path(
            path,
            {"Python"},
            categories,
            {},
        )
        skills_high = {
            "Python",
            "FastAPI",
            "Docker",
            "Kubernetes",
            "Terraform",
            "AWS",
        }
        high = score_path(
            path,
            skills_high,
            categories,
            {},
        )
        assert high >= low


# ── Intelligence Endpoint Tests ────────────────────────────────────────


def test_analyze_requires_github_user(client: TestClient) -> None:
    """通常ユーザー（非 GitHub）で analyze を呼ぶと 403 になること。"""
    headers = auth_header(client, "normal_analyze")
    resp = client.post(
        "/api/intelligence/analyze",
        json={"include_forks": False},
        headers=headers,
    )
    assert resp.status_code == 403


def test_summarize_requires_auth(client: TestClient) -> None:
    """認証なしで summarize を呼ぶと 401 になること。"""
    resp = client.post(
        "/api/intelligence/summarize",
        json={
            "analysis": {
                "username": "test",
                "repos_analyzed": 0,
                "unique_skills": 0,
                "analyzed_at": "2024-01-01T00:00:00",
                "languages": {},
            }
        },
    )
    assert resp.status_code == 401


def test_skill_activity_requires_github_user(client: TestClient) -> None:
    """通常ユーザーで skill-activity を呼ぶと 403 になること。"""
    headers = auth_header(client, "normal_skill")
    resp = client.post(
        "/api/intelligence/skill-activity",
        headers=headers,
    )
    assert resp.status_code == 403


# ── Response Mapper Tests ──────────────────────────────────────────────


def test_map_pipeline_result_includes_languages() -> None:
    """languages フィールドが正しくマッピングされること。"""
    result = IntelligenceResult(
        username="testuser",
        repos_analyzed=3,
        unique_skills=5,
        analyzed_at="2024-01-01T00:00:00",
        languages={"Python": 50000, "TypeScript": 30000},
    )
    response = map_pipeline_result(result)
    assert response.languages == {"Python": 50000, "TypeScript": 30000}
    assert response.username == "testuser"
    assert response.repos_analyzed == 3
