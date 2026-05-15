"""AI キャリア分析タスクのハンドラ。"""

import json
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from ....core.logging_utils import get_logger
from ....models.career_analysis import CareerAnalysis
from .base import TaskHandler

logger = get_logger(__name__)


def _now() -> datetime:
    return datetime.now(timezone.utc)


class CareerAnalysisHandler(TaskHandler):
    """AI キャリアパス分析タスク。"""

    def get_record(self, db: Session, payload: dict) -> CareerAnalysis | None:
        user_id = payload.get("user_id")
        record_id = payload.get("record_id")
        if not user_id or not record_id:
            return None
        return db.query(CareerAnalysis).filter_by(id=record_id, user_id=user_id).first()

    async def run(self, db: Session, payload: dict) -> None:
        from ...career_analysis.builder import build_career_analysis
        from ...intelligence.llm import get_llm_client

        user_id = payload["user_id"]
        record_id = payload["record_id"]
        target_position = payload["target_position"]

        analysis = db.query(CareerAnalysis).filter_by(id=record_id, user_id=user_id).first()
        if not analysis:
            logger.error("キャリア分析レコードが見つかりません", extra={"record_id": record_id})
            return

        analysis.status = "processing"
        analysis.started_at = _now()
        db.commit()

        llm_client = get_llm_client()
        try:
            result = await build_career_analysis(
                db=db,
                user_id=user_id,
                target_position=target_position,
                llm_client=llm_client,
            )
        except ValueError as exc:
            analysis.status = "dead_letter"
            analysis.error_message = str(exc)
            analysis.completed_at = _now()
            db.commit()
            raise exc

        analysis.result_json = json.dumps(result, ensure_ascii=False)
        analysis.status = "completed"
        analysis.error_message = None
        analysis.completed_at = _now()
        db.commit()
