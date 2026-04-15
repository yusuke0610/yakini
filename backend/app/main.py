import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException, Request, Response  # noqa: E402
from fastapi.exceptions import RequestValidationError  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.responses import JSONResponse  # noqa: E402
from slowapi.errors import RateLimitExceeded  # noqa: E402
from starlette.middleware.base import BaseHTTPMiddleware  # noqa: E402

from .core.errors import (  # noqa: E402
    ErrorCode,
    build_app_error_response,
    generate_error_id,
    normalize_http_exception_detail,
)
from .core.logging_utils import setup_logging  # noqa: E402
from .core.messages import get_error, load_messages  # noqa: E402
from .core.security.csrf import CSRFMiddleware  # noqa: E402
from .core.security.dependencies import limiter  # noqa: E402
from .core.settings import get_cors_origins  # noqa: E402
from .db.bootstrap import bootstrap  # noqa: E402
from .middleware.request_id import RequestIDMiddleware  # noqa: E402
from .routers import (  # noqa: E402
    admin_router,
    auth_router,
    blog_router,
    career_analysis_router,
    health_router,
    intelligence_router,
    internal_router,
    master_data_router,
    notifications_router,
    resumes_router,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    setup_logging()
    load_messages()
    if os.getenv("APP_BOOTSTRAPPED", "0") != "1":
        bootstrap()
    yield


app = FastAPI(title="Resume Builder API", lifespan=lifespan)
app.state.limiter = limiter
logger = logging.getLogger(__name__)


@app.exception_handler(RateLimitExceeded)
async def _rate_limit_handler(request: Request, exc: RateLimitExceeded):
    retry_after = (
        getattr(exc, "headers", {}).get("Retry-After") if hasattr(exc, "headers") else None
    )
    error_id = generate_error_id()
    logger.warning(
        "リクエストレート制限",
        extra={"http_status": 429, "error_id": error_id, "status": "failed"},
    )
    return JSONResponse(
        status_code=429,
        content=build_app_error_response(
            code=ErrorCode.RATE_LIMITED,
            message=get_error("server.rate_limited"),
            action="しばらく待ってから再試行してください",
            retry_after=int(retry_after) if retry_after and str(retry_after).isdigit() else None,
            error_id=error_id,
        ).model_dump(exclude_none=True),
    )


@app.exception_handler(RequestValidationError)
async def _validation_exception_handler(request: Request, exc: RequestValidationError):
    error_id = generate_error_id()
    logger.warning(
        "リクエストバリデーションエラー",
        extra={"http_status": 422, "error_id": error_id, "status": "failed"},
    )
    return JSONResponse(
        status_code=422,
        content=build_app_error_response(
            code=ErrorCode.VALIDATION_ERROR,
            message="入力内容を確認してください。",
            action="入力内容を見直して再試行してください",
            error_id=error_id,
        ).model_dump(exclude_none=True),
    )


@app.exception_handler(HTTPException)
async def _http_exception_handler(request: Request, exc: HTTPException):
    error_id = generate_error_id()
    payload = normalize_http_exception_detail(
        status_code=exc.status_code,
        detail=exc.detail,
        error_id=error_id,
    )
    log_level = logging.WARNING if exc.status_code < 500 else logging.ERROR
    logger.log(
        log_level,
        "HTTPエラー応答",
        extra={"http_status": exc.status_code, "error_id": payload.error_id, "status": "failed"},
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=payload.model_dump(exclude_none=True),
        headers=exc.headers,
    )


@app.exception_handler(Exception)
async def _unhandled_exception_handler(request: Request, exc: Exception):
    error_id = generate_error_id()
    logger.exception(
        "未処理例外",
        extra={"http_status": 500, "error_id": error_id, "status": "failed"},
    )
    return JSONResponse(
        status_code=500,
        content=build_app_error_response(
            code=ErrorCode.INTERNAL_ERROR,
            message=get_error("server.internal_error"),
            action="ページを再読み込みして、解消しない場合は時間を置いて再試行してください",
            error_id=error_id,
        ).model_dump(exclude_none=True),
    )


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """レスポンスにセキュリティヘッダーを付与するミドルウェア。"""

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: blob:; "
            "font-src 'self'; "
            "connect-src 'self' https://api.github.com https://github.com; "
            "frame-ancestors 'none'"
        )
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        return response


app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(CSRFMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-CSRF-Token", "X-Request-ID"],
)
# RequestIDMiddleware は最後に追加することで最初に実行される（ミドルウェアは逆順）
app.add_middleware(RequestIDMiddleware)

app.include_router(health_router)
app.include_router(career_analysis_router)
app.include_router(auth_router)
app.include_router(resumes_router)
app.include_router(intelligence_router)
app.include_router(blog_router)
app.include_router(master_data_router)
app.include_router(notifications_router)
app.include_router(admin_router)
app.include_router(internal_router)
