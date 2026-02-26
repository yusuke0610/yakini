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

from .auth import create_access_token, get_current_user, verify_password
from .bootstrap import bootstrap
from .database import get_db
from .logging_utils import log_event
from .models import User
from .repositories import (
    BasicInfoRepository,
    ResumeRepository,
    ResumeRepository,
    UserRepository,
)
from .schemas import (
    BasicInfoCreate,
    BasicInfoResponse,
    BasicInfoUpdate,
    LoginRequest,
    ResumeCreate,
    ResumeResponse,
    ResumeUpdate,
    ResumeCreate,
    ResumeResponse,
    ResumeUpdate,
    TokenResponse,
)
from .settings import get_admin_token, get_cors_origins
from .services.pdf_generator import build_Resume_pdf, build_resume_pdf
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


@app.post(
    "/api/basic-info", response_model=BasicInfoResponse, status_code=201
)
def create_basic_info(
    payload: BasicInfoCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> BasicInfoResponse:
    repository = BasicInfoRepository(db)
    return repository.create(payload.model_dump())


@app.get("/api/basic-info/latest", response_model=BasicInfoResponse)
def get_latest_basic_info(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> BasicInfoResponse:
    repository = BasicInfoRepository(db)
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
    _: User = Depends(get_current_user),
) -> BasicInfoResponse:
    repository = BasicInfoRepository(db)
    basic_info = repository.get_by_id(str(basic_info_id))
    if not basic_info:
        raise HTTPException(status_code=404, detail="Basic info not found")

    return repository.update(basic_info, payload.model_dump())


@app.post("/api/resumes", response_model=ResumeResponse, status_code=201)
def create_resume(
    payload: ResumeCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> ResumeResponse:
    repository = ResumeRepository(db)
    return repository.create(payload.model_dump())


@app.get("/api/resumes/{resume_id}", response_model=ResumeResponse)
def get_resume(
    resume_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> ResumeResponse:
    repository = ResumeRepository(db)
    resume = repository.get_by_id(str(resume_id))
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    return resume


@app.put("/api/resumes/{resume_id}", response_model=ResumeResponse)
def update_resume(
    resume_id: uuid.UUID,
    payload: ResumeUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> ResumeResponse:
    repository = ResumeRepository(db)
    resume = repository.get_by_id(str(resume_id))
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    return repository.update(resume, payload.model_dump())


@app.get("/api/resumes/{resume_id}/pdf")
def download_resume_pdf(
    resume_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> StreamingResponse:
    resume_repository = ResumeRepository(db)
    basic_info_repository = BasicInfoRepository(db)

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


@app.post(
    "/api/Resume", response_model=ResumeResponse, status_code=201
)
def create_Resume(
    payload: ResumeCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> ResumeResponse:
    repository = ResumeRepository(db)
    return repository.create(payload.model_dump())


@app.get("/api/Resume/{Resume_id}", response_model=ResumeResponse)
def get_Resume(
    Resume_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> ResumeResponse:
    repository = ResumeRepository(db)
    Resume = repository.get_by_id(str(Resume_id))
    if not Resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    return Resume


@app.put(
    "/api/Resume/{Resume_id}", response_model=ResumeResponse
)
def update_Resume(
    Resume_id: uuid.UUID,
    payload: ResumeUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> ResumeResponse:
    repository = ResumeRepository(db)
    Resume = repository.get_by_id(str(Resume_id))
    if not Resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    return repository.update(Resume, payload.model_dump())


@app.get("/api/Resume/{Resume_id}/pdf")
def download_Resume_pdf(
    Resume_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> StreamingResponse:
    Resume_repository = ResumeRepository(db)
    basic_info_repository = BasicInfoRepository(db)

    Resume = Resume_repository.get_by_id(str(Resume_id))
    if not Resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    basic_info = basic_info_repository.get_latest()

    payload = {
        "full_name": basic_info.full_name if basic_info else "",
        "record_date": basic_info.record_date if basic_info else "",
        "qualifications": basic_info.qualifications if basic_info else [],
        "postal_code": Resume.postal_code,
        "prefecture": Resume.prefecture,
        "address": Resume.address,
        "email": Resume.email,
        "phone": Resume.phone,
        "motivation": Resume.motivation,
        "educations": Resume.educations,
        "work_histories": Resume.work_histories,
    }
    pdf_bytes = build_Resume_pdf(payload)

    headers = {
        "Content-Disposition": (
            f'attachment; filename="Resume-{Resume.id}.pdf"'
        ),
    }
    return StreamingResponse(
        io.BytesIO(pdf_bytes), media_type="application/pdf", headers=headers
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
