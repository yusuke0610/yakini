import io
import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..models import User
from ..repositories import BasicInfoRepository, ResumeRepository
from ..schemas import ResumeCreate, ResumeResponse, ResumeUpdate
from ..services.markdown.markdown_service import (
    generate_resume_markdown as build_resume_markdown,
)
from ..services.pdf.pdf_service import generate_resume as build_resume_pdf

router = APIRouter(prefix="/api/resumes", tags=["resumes"])


@router.post("", response_model=ResumeResponse, status_code=201)
def create_resume(
    payload: ResumeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ResumeResponse:
    repository = ResumeRepository(db, current_user.id)
    return repository.create(payload.model_dump())


@router.get("/latest", response_model=ResumeResponse)
def get_latest_resume(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ResumeResponse:
    repository = ResumeRepository(db, current_user.id)
    resume = repository.get_latest()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
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
        raise HTTPException(status_code=404, detail="Resume not found")
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
        raise HTTPException(status_code=404, detail="Resume not found")

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
