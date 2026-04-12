"""LLM ポジションアドバイスサービス。

キャッシュ検証・データ取得・LLMプロンプト構築・キャッシュ書き込みのロジックを
router から分離する。
"""

from sqlalchemy.orm import Session

from ...models import GitHubAnalysisCache
from ..llm.sanitizer import strip_prohibited_fields
from .llm_summarizer import check_llm_available, generate_learning_advice


class LLMPositionAdviceService:
    """GitHub 分析結果をもとに LLM でポジションアドバイスを生成するサービスクラス。"""

    def __init__(self, db: Session, user_id: str) -> None:
        self._db = db
        self._user_id = user_id

    def _get_cache(self) -> GitHubAnalysisCache | None:
        """ユーザーの GitHub 分析キャッシュを返す。"""
        return self._db.query(GitHubAnalysisCache).filter_by(user_id=self._user_id).first()

    def has_analysis(self) -> bool:
        """分析結果キャッシュが存在するかを返す。"""
        cache = self._get_cache()
        return cache is not None and bool(cache.analysis_result)

    def has_position_scores(self) -> bool:
        """ポジションスコアが存在するかを返す。"""
        cache = self._get_cache()
        if not cache or not cache.analysis_result:
            return False
        return bool(cache.analysis_result.get("position_scores"))

    async def generate_and_save(self) -> str | None:
        """
        LLM でポジションアドバイスを生成してキャッシュに保存する。

        LLM が利用不可または生成失敗の場合は None を返す。
        """
        cache = self._get_cache()
        if not cache or not cache.analysis_result:
            return None

        analysis = cache.analysis_result
        scores = analysis.get("position_scores")
        if not scores:
            return None

        available = await check_llm_available()
        if not available:
            return None

        # C分類フィールド（username 等）を防御的に除去してから LLM に渡す
        sanitized_analysis = strip_prohibited_fields(analysis)
        advice = await generate_learning_advice(sanitized_analysis, scores)
        if not advice:
            return None

        cache.position_advice = advice
        self._db.commit()

        return advice
