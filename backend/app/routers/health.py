import logging

from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.settings import get_app_version
from app.db.database import get_db

router = APIRouter(tags=["health"])
logger = logging.getLogger(__name__)


@router.get("/health")
def healthcheck(db: Session = Depends(get_db)) -> dict[str, str]:
    """ヘルスチェック。Uptime Check から呼ばれる。DB 接続も検証する。"""
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        logger.error("ヘルスチェック: DB 接続失敗", exc_info=True)
        raise HTTPException(status_code=503, detail="Service Unavailable")
    return {"status": "ok", "version": get_app_version()}
