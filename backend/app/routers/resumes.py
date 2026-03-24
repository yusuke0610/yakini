import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..messages import get_error
from ..models import User
from ..repositories import BasicInfoRepository, ResumeRepository
from ..schemas import ResumeCreate, ResumeResponse, ResumeUpdate
from ..services.markdown.generators.resume_generator import (
    build_resume_markdown,
)
from ..services.pdf.generators.resume_generator import build_resume_pdf
from .download_utils import stream_markdown, stream_pdf

router = APIRouter(prefix="/api/resumes", tags=["resumes"])


@router.post("", response_model=ResumeResponse, status_code=201)
def create_resume(
    payload: ResumeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ResumeResponse:
    repository = ResumeRepository(db, current_user.id)
    try:
        return repository.create(payload.model_dump())
    except ValueError as exc:
        raise HTTPException(
            status_code=409,
            detail=get_error(str(exc), document="職務経歴書"),
        ) from exc


@router.get("/latest", response_model=ResumeResponse)
def get_latest_resume(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ResumeResponse:
    repository = ResumeRepository(db, current_user.id)
    resume = repository.get_latest()
    if not resume:
        raise HTTPException(
            status_code=404,
            detail=get_error("document.not_found", document="職務経歴書"),
        )
    return resume


@router.get("/{resume_id}", response_model=ResumeResponse)
def get_resume(
    resume_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ResumeResponse:
    repository = ResumeRepository(db, current_user.id)
    resume = repository.get_by_id(str(resume_id))
    if not resume:
        raise HTTPException(
            status_code=404,
            detail=get_error("document.not_found", document="職務経歴書"),
        )
    return resume


@router.put("/{resume_id}", response_model=ResumeResponse)
def update_resume(
    resume_id: uuid.UUID,
    payload: ResumeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ResumeResponse:
    repository = ResumeRepository(db, current_user.id)
    resume = repository.get_by_id(str(resume_id))
    if not resume:
        raise HTTPException(
            status_code=404,
            detail=get_error("document.not_found", document="職務経歴書"),
        )

    return repository.update(resume, payload.model_dump())


@router.get("/{resume_id}/pdf")
def download_resume_pdf(
    resume_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    resume_repository = ResumeRepository(db, current_user.id)
    basic_info_repository = BasicInfoRepository(db, current_user.id)

    resume = resume_repository.get_by_id(str(resume_id))
    if not resume:
        raise HTTPException(
            status_code=404,
            detail=get_error("document.not_found", document="職務経歴書"),
        )

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
    return stream_pdf(pdf_bytes, f"career-resume-{resume.id}.pdf")


@router.get("/{resume_id}/markdown")
def download_resume_markdown(
    resume_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    resume_repository = ResumeRepository(db, current_user.id)
    basic_info_repository = BasicInfoRepository(db, current_user.id)

    resume = resume_repository.get_by_id(str(resume_id))
    if not resume:
        raise HTTPException(
            status_code=404,
            detail=get_error("document.not_found", document="職務経歴書"),
        )

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
    return stream_markdown(md_text, f"career-resume-{resume.id}.md")
