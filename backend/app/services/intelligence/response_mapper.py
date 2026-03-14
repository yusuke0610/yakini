from ...schemas_intelligence import (
    AnalysisResponse,
    CareerPredictionResponse,
    CareerSimulationResponse,
    PredictedRoleItem,
    SimulatedPathItem,
    SkillGrowthItem,
    SkillTimelineItem,
    YearSnapshotItem,
)
from .pipeline import IntelligenceResult


def _map_role(role) -> PredictedRoleItem:
    return PredictedRoleItem(
        role_name=role.role_name,
        confidence=role.confidence,
        matching_skills=role.matching_skills,
        missing_skills=role.missing_skills,
        seniority=role.seniority,
    )


def map_pipeline_result(result: IntelligenceResult) -> AnalysisResponse:
    return AnalysisResponse(
        username=result.username,
        repos_analyzed=result.repos_analyzed,
        unique_skills=result.unique_skills,
        timelines=[
            SkillTimelineItem(
                skill_name=t.skill_name,
                category=t.category,
                first_seen=t.first_seen,
                last_seen=t.last_seen,
                usage_frequency=t.usage_frequency,
                repositories=t.repositories,
                yearly_usage=t.yearly_usage,
            )
            for t in result.timelines
        ],
        year_snapshots=[
            YearSnapshotItem(
                year=s.year,
                skills=s.skills,
                new_skills=s.new_skills,
            )
            for s in result.year_snapshots
        ],
        growth=[
            SkillGrowthItem(
                skill_name=g.skill_name,
                category=g.category,
                trend=g.trend.value,
                velocity=g.velocity,
                yearly_usage=g.yearly_usage,
                first_seen=g.first_seen,
                last_seen=g.last_seen,
                total_repos=g.total_repos,
            )
            for g in result.growth
        ],
        prediction=CareerPredictionResponse(
            current_role=_map_role(result.prediction.current_role),
            next_roles=[_map_role(r) for r in result.prediction.next_roles],
            long_term_roles=[
                _map_role(r) for r in result.prediction.long_term_roles
            ],
            skill_summary=result.prediction.skill_summary,
        ),
        simulation=CareerSimulationResponse(
            current_role=result.simulation.current_role,
            paths=[
                SimulatedPathItem(
                    path=p.path,
                    confidence=p.confidence,
                    description=p.description,
                )
                for p in result.simulation.paths
            ],
            total_paths_explored=result.simulation.total_paths_explored,
        ),
        analyzed_at=result.analyzed_at,
    )
