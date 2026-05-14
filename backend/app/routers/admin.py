import logging

from fastapi import APIRouter, Depends, HTTPException

from ..core.messages import get_error
from ..core.security.dependencies import verify_admin_token
from ..core.settings import get_turso_database_url
from ..db.sqlite_backup import backup_sqlite_to_gcs

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/backup")
def admin_backup(
    _: None = Depends(verify_admin_token),
) -> dict[str, str]:
    # Turso (libSQL) モード時は GCS への SQLite バックアップが無効。
    # Issue 3 のインフラ移行で本エンドポイント自体を廃止する予定
    if get_turso_database_url():
        raise HTTPException(
            status_code=409,
            detail="Turso モードでは SQLite の GCS バックアップは無効です。",
        )
    try:
        return backup_sqlite_to_gcs()
    except RuntimeError as error:
        logging.warning("sqlite backup runtime error: %s", error)
        raise HTTPException(
            status_code=503,
            detail=get_error("server.backup_service_unavailable"),
        ) from error
    except Exception as error:
        logging.exception("sqlite backup failed")
        raise HTTPException(status_code=500, detail=get_error("server.backup_failed")) from error
