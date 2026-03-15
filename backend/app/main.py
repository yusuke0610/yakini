import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware

from .bootstrap import bootstrap
from .dependencies import limiter
from .routers import (
    admin_router,
    auth_router,
    basic_info_router,
    health_router,
    intelligence_router,
    resumes_router,
    rirekisho_router,
)
from .settings import get_cors_origins


@asynccontextmanager
async def lifespan(_: FastAPI):
    if os.getenv("APP_BOOTSTRAPPED", "0") != "1":
        bootstrap()
    yield


app = FastAPI(title="Resume Builder API", lifespan=lifespan)
app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def _rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "リクエストが多すぎます。しばらくしてからお試しください。"},
    )


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """レスポンスにセキュリティヘッダーを付与するミドルウェア。"""

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response


app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(basic_info_router)
app.include_router(resumes_router)
app.include_router(rirekisho_router)
app.include_router(intelligence_router)
app.include_router(admin_router)
