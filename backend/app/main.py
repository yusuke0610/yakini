import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, Request, Response  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.responses import JSONResponse  # noqa: E402
from slowapi.errors import RateLimitExceeded  # noqa: E402
from starlette.middleware.base import BaseHTTPMiddleware  # noqa: E402

from .bootstrap import bootstrap  # noqa: E402
from .csrf import CSRFMiddleware  # noqa: E402
from .dependencies import limiter  # noqa: E402
from .messages import get_error, load_messages  # noqa: E402
from .routers import (  # noqa: E402
    admin_router,
    auth_router,
    basic_info_router,
    blog_router,
    health_router,
    intelligence_router,
    master_data_router,
    resumes_router,
    rirekisho_router,
)
from .settings import get_cors_origins  # noqa: E402


@asynccontextmanager
async def lifespan(_: FastAPI):
    load_messages()
    if os.getenv("APP_BOOTSTRAPPED", "0") != "1":
        bootstrap()
    yield


app = FastAPI(title="Resume Builder API", lifespan=lifespan)
app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def _rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": get_error("server.rate_limited")},
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
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-CSRF-Token"],
)

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(basic_info_router)
app.include_router(resumes_router)
app.include_router(rirekisho_router)
app.include_router(intelligence_router)
app.include_router(blog_router)
app.include_router(master_data_router)
app.include_router(admin_router)
