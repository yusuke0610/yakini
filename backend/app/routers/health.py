from fastapi import APIRouter

from app.core.settings import get_app_version

router = APIRouter(tags=["health"])


@router.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok", "version": get_app_version()}
