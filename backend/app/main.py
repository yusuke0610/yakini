import io
import logging
import os
import uuid
from contextlib import asynccontextmanager

from dotenv import load_dotenv

load_dotenv()

from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from .auth import create_access_token, get_current_user, hash_password, verify_password
from .bootstrap import bootstrap
from .database import get_db
from .logging_utils import log_event
from .models import User
from .repositories import (
    BasicInfoRepository,
    ResumeRepository,
    RirekishoRepository,
    UserRepository,
)
from .schemas import (
    BasicInfoCreate,
    BasicInfoResponse,
    BasicInfoUpdate,
    GitHubCallbackRequest,
    LoginRequest,
    RegisterRequest,
    ResumeCreate,
    ResumeResponse,
    ResumeUpdate,
    RirekishoCreate,
    RirekishoResponse,
    RirekishoUpdate,
    TokenResponse,
)
from .settings import get_admin_token, get_cors_origins, get_github_client_id, get_github_client_secret
from .services.markdown.markdown_service import generate_resume_markdown as build_resume_markdown, generate_rirekisho_markdown as build_rirekisho_markdown
from .services.pdf.pdf_service import generate_resume as build_resume_pdf, generate_rirekisho as build_rirekisho_pdf
from .services.sqlite_backup import backup_sqlite_to_gcs


@asynccontextmanager
async def lifespan(_: FastAPI):
    if os.getenv("APP_BOOTSTRAPPED", "0") != "1":
        bootstrap()
    yield


app = FastAPI(title="Resume Builder API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _verify_admin_token(
    authorization: str | None = Header(default=None),
) -> None:
    configured_token = get_admin_token()
    if not configured_token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ADMIN_TOKEN is not configured",
        )

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
        )

    provided_token = authorization.removeprefix("Bearer ").strip()
    if provided_token != configured_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid admin token",
        )


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/auth/register", response_model=TokenResponse, status_code=201)
def register(
    payload: RegisterRequest, db: Session = Depends(get_db)
) -> TokenResponse:
    repo = UserRepository(db)
    if repo.get_by_username(payload.username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="このユーザー名は既に使用されています",
        )
    if repo.get_by_email(payload.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="このメールアドレスは既に使用されています",
        )
    user = repo.create(payload.username, hash_password(payload.password), email=payload.email)
    token = create_access_token(user.username)
    return TokenResponse(access_token=token)


@app.post("/auth/login", response_model=TokenResponse)
def login(
    payload: LoginRequest, db: Session = Depends(get_db)
) -> TokenResponse:
    print("ログイン開始")
    user = UserRepository(db).get_by_username(payload.username)
    if not user or not verify_password(
        payload.password, user.hashed_password
    ):
        log_event(
            logging.WARNING,
            "login_failed",
            username=payload.username,
            reason="invalid username or password",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="ユーザー名またはパスワードが正しくありません",
        )
    token = create_access_token(user.username)
    return TokenResponse(access_token=token)


@app.post("/auth/github/callback", response_model=TokenResponse)
async def github_callback(
    payload: GitHubCallbackRequest, db: Session = Depends(get_db)
) -> TokenResponse:
    client_id = get_github_client_id()
    client_secret = get_github_client_secret()
    if not client_id or not client_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GitHub OAuth is not configured",
        )

    import httpx

    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            "https://github.com/login/oauth/access_token",
            json={
                "client_id": client_id,
                "client_secret": client_secret,
                "code": payload.code,
            },
            headers={"Accept": "application/json"},
        )
        token_data = token_resp.json()
        access_token = token_data.get("access_token")
        if not access_token:
            log_event(
                logging.WARNING,
                "github_oauth_failed",
                error=token_data.get("error_description", "unknown"),
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="GitHub認証に失敗しました",
            )

        user_resp = await client.get(
            "https://api.github.com/user",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github+json",
            },
        )
        github_user = user_resp.json()

    github_id = github_user.get("id")
    github_login = github_user.get("login")
    if not github_id or not github_login:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="GitHubユーザー情報の取得に失敗しました",
        )

    repo = UserRepository(db)
    user = repo.get_by_github_id(github_id)
    if not user:
        user = repo.create_github_user(
            username=f"github:{github_login}", github_id=github_id
        )
        log_event(logging.INFO, "github_user_created", username=user.username)

    token = create_access_token(user.username)
    return TokenResponse(access_token=token)


@app.post(
    "/api/basic-info", response_model=BasicInfoResponse, status_code=201
)
def create_basic_info(
    payload: BasicInfoCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BasicInfoResponse:
    repository = BasicInfoRepository(db, current_user.id)
    return repository.create(payload.model_dump())


@app.get("/api/basic-info/latest", response_model=BasicInfoResponse)
def get_latest_basic_info(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BasicInfoResponse:
    repository = BasicInfoRepository(db, current_user.id)
    basic_info = repository.get_latest()
    if not basic_info:
        raise HTTPException(status_code=404, detail="Basic info not found")
    return basic_info


@app.put(
    "/api/basic-info/{basic_info_id}", response_model=BasicInfoResponse
)
def update_basic_info(
    basic_info_id: uuid.UUID,
    payload: BasicInfoUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BasicInfoResponse:
    repository = BasicInfoRepository(db, current_user.id)
    basic_info = repository.get_by_id(str(basic_info_id))
    if not basic_info:
        raise HTTPException(status_code=404, detail="Basic info not found")

    return repository.update(basic_info, payload.model_dump())


@app.post("/api/resumes", response_model=ResumeResponse, status_code=201)
def create_resume(
    payload: ResumeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ResumeResponse:
    repository = ResumeRepository(db, current_user.id)
    return repository.create(payload.model_dump())


@app.get("/api/resumes/latest", response_model=ResumeResponse)
def get_latest_resume(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ResumeResponse:
    repository = ResumeRepository(db, current_user.id)
    resume = repository.get_latest()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    return resume


@app.get("/api/resumes/{resume_id}", response_model=ResumeResponse)
def get_resume(
    resume_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ResumeResponse:
    repository = ResumeRepository(db, current_user.id)
    resume = repository.get_by_id(str(resume_id))
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    return resume


@app.put("/api/resumes/{resume_id}", response_model=ResumeResponse)
def update_resume(
    resume_id: uuid.UUID,
    payload: ResumeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ResumeResponse:
    repository = ResumeRepository(db, current_user.id)
    resume = repository.get_by_id(str(resume_id))
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    return repository.update(resume, payload.model_dump())


@app.get("/api/resumes/{resume_id}/pdf")
def download_resume_pdf(
    resume_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    resume_repository = ResumeRepository(db, current_user.id)
    basic_info_repository = BasicInfoRepository(db, current_user.id)

    resume = resume_repository.get_by_id(str(resume_id))
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    basic_info = basic_info_repository.get_latest()

    payload = {
        "full_name": basic_info.full_name if basic_info else "",
        "record_date": basic_info.record_date if basic_info else "",
        "qualifications": basic_info.qualifications if basic_info else [],
        "career_summary": resume.career_summary,
        "self_pr": resume.self_pr,
        "experiences": resume.experiences,
    }
    pdf_bytes = build_resume_pdf(payload)

    headers = {
        "Content-Disposition": (
            f'attachment; filename="career-resume-{resume.id}.pdf"'
        ),
    }
    return StreamingResponse(
        io.BytesIO(pdf_bytes), media_type="application/pdf", headers=headers
    )


@app.get("/api/resumes/{resume_id}/markdown")
def download_resume_markdown(
    resume_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    resume_repository = ResumeRepository(db, current_user.id)
    basic_info_repository = BasicInfoRepository(db, current_user.id)

    resume = resume_repository.get_by_id(str(resume_id))
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    basic_info = basic_info_repository.get_latest()

    payload = {
        "full_name": basic_info.full_name if basic_info else "",
        "record_date": basic_info.record_date if basic_info else "",
        "qualifications": basic_info.qualifications if basic_info else [],
        "career_summary": resume.career_summary,
        "self_pr": resume.self_pr,
        "experiences": resume.experiences,
    }
    md_text = build_resume_markdown(payload)

    headers = {
        "Content-Disposition": (
            f'attachment; filename="career-resume-{resume.id}.md"'
        ),
    }
    return StreamingResponse(
        io.BytesIO(md_text.encode("utf-8")),
        media_type="text/markdown; charset=utf-8",
        headers=headers,
    )


@app.post("/api/rirekisho", response_model=RirekishoResponse, status_code=201)
def create_rirekisho(
    payload: RirekishoCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RirekishoResponse:
    repository = RirekishoRepository(db, current_user.id)
    return repository.create(payload.model_dump())


@app.get("/api/rirekisho/latest", response_model=RirekishoResponse)
def get_latest_rirekisho(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RirekishoResponse:
    repository = RirekishoRepository(db, current_user.id)
    rirekisho = repository.get_latest()
    if not rirekisho:
        raise HTTPException(status_code=404, detail="Rirekisho not found")
    return rirekisho


@app.get("/api/rirekisho/{rirekisho_id}", response_model=RirekishoResponse)
def get_rirekisho(
    rirekisho_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RirekishoResponse:
    repository = RirekishoRepository(db, current_user.id)
    rirekisho = repository.get_by_id(str(rirekisho_id))
    if not rirekisho:
        raise HTTPException(status_code=404, detail="Rirekisho not found")
    return rirekisho


@app.put("/api/rirekisho/{rirekisho_id}", response_model=RirekishoResponse)
def update_rirekisho(
    rirekisho_id: uuid.UUID,
    payload: RirekishoUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RirekishoResponse:
    repository = RirekishoRepository(db, current_user.id)
    rirekisho = repository.get_by_id(str(rirekisho_id))
    if not rirekisho:
        raise HTTPException(status_code=404, detail="Rirekisho not found")

    return repository.update(rirekisho, payload.model_dump())


@app.get("/api/rirekisho/{rirekisho_id}/pdf")
def download_rirekisho_pdf(
    rirekisho_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    rirekisho_repository = RirekishoRepository(db, current_user.id)
    basic_info_repository = BasicInfoRepository(db, current_user.id)

    rirekisho = rirekisho_repository.get_by_id(str(rirekisho_id))
    if not rirekisho:
        raise HTTPException(status_code=404, detail="Rirekisho not found")

    basic_info = basic_info_repository.get_latest()

    payload = {
        "full_name": basic_info.full_name if basic_info else "",
        "record_date": basic_info.record_date if basic_info else "",
        "qualifications": basic_info.qualifications if basic_info else [],
        "postal_code": rirekisho.postal_code,
        "prefecture": rirekisho.prefecture,
        "address": rirekisho.address,
        "email": rirekisho.email,
        "phone": rirekisho.phone,
        "motivation": rirekisho.motivation,
        "photo": rirekisho.photo,
        "educations": rirekisho.educations,
        "work_histories": rirekisho.work_histories,
    }
    pdf_bytes = build_rirekisho_pdf(payload)

    headers = {
        "Content-Disposition": (
            f'attachment; filename="rirekisho-{rirekisho.id}.pdf"'
        ),
    }
    return StreamingResponse(
        io.BytesIO(pdf_bytes), media_type="application/pdf", headers=headers
    )


@app.get("/api/rirekisho/{rirekisho_id}/markdown")
def download_rirekisho_markdown(
    rirekisho_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    rirekisho_repository = RirekishoRepository(db, current_user.id)
    basic_info_repository = BasicInfoRepository(db, current_user.id)

    rirekisho = rirekisho_repository.get_by_id(str(rirekisho_id))
    if not rirekisho:
        raise HTTPException(status_code=404, detail="Rirekisho not found")

    basic_info = basic_info_repository.get_latest()

    payload = {
        "full_name": basic_info.full_name if basic_info else "",
        "record_date": basic_info.record_date if basic_info else "",
        "qualifications": basic_info.qualifications if basic_info else [],
        "postal_code": rirekisho.postal_code,
        "prefecture": rirekisho.prefecture,
        "address": rirekisho.address,
        "email": rirekisho.email,
        "phone": rirekisho.phone,
        "motivation": rirekisho.motivation,
        "educations": rirekisho.educations,
        "work_histories": rirekisho.work_histories,
    }
    md_text = build_rirekisho_markdown(payload)

    headers = {
        "Content-Disposition": (
            f'attachment; filename="rirekisho-{rirekisho.id}.md"'
        ),
    }
    return StreamingResponse(
        io.BytesIO(md_text.encode("utf-8")),
        media_type="text/markdown; charset=utf-8",
        headers=headers,
    )


@app.post("/admin/backup")
def admin_backup(
    _: None = Depends(_verify_admin_token),
) -> dict[str, str]:
    try:
        return backup_sqlite_to_gcs()
    except RuntimeError as error:
        raise HTTPException(
            status_code=503, detail=str(error)
        ) from error
    except Exception as error:
        logging.exception("sqlite backup failed")
        raise HTTPException(
            status_code=500, detail="Backup failed"
        ) from error
