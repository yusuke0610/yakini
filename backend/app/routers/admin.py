import logging

from fastapi import APIRouter, Depends, HTTPException

from ..dependencies import verify_admin_token
from ..messages import get_error
from ..services.sqlite_backup import backup_sqlite_to_gcs

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/backup")
def admin_backup(
    _: None = Depends(verify_admin_token),
) -> dict[str, str]:
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
