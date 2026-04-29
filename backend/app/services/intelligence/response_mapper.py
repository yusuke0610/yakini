from ...schemas.intelligence import AnalysisResponse, PositionScoresResponse
from .pipeline import IntelligenceResult


def map_pipeline_result(result: IntelligenceResult) -> AnalysisResponse:
    """
    パイプラインの実行結果を API レスポンス形式に変換します。
    """
    position_scores = None
    if result.position_scores:
        ps = result.position_scores
        position_scores = PositionScoresResponse(
            backend=ps.backend,
            frontend=ps.frontend,
            fullstack=ps.fullstack,
            sre=ps.sre,
            cloud=ps.cloud,
            missing_skills=ps.missing_skills,
        )

    return AnalysisResponse(
        username=result.username,
        repos_analyzed=result.repos_analyzed,
        unique_skills=result.unique_skills,
        analyzed_at=result.analyzed_at,
        languages=result.languages,
        detected_frameworks=result.detected_frameworks,
        position_scores=position_scores,
    )
