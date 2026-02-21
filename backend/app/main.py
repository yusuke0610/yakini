import io
import os
import uuid

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from .models import BasicInfo, Resume, Rirekisho
from .schemas import (
    BasicInfoCreate,
    BasicInfoResponse,
    BasicInfoUpdate,
    RirekishoCreate,
    RirekishoResponse,
    RirekishoUpdate,
    ResumeCreate,
    ResumeResponse,
    ResumeUpdate,
)
from .services.pdf_generator import build_rirekisho_pdf, build_resume_pdf

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Resume Builder API")

cors_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _get_latest_basic_info(db: Session) -> BasicInfo | None:
    statement = select(BasicInfo).order_by(BasicInfo.updated_at.desc()).limit(1)
    return db.scalar(statement)


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/basic-info", response_model=BasicInfoResponse, status_code=201)
def create_basic_info(payload: BasicInfoCreate, db: Session = Depends(get_db)) -> BasicInfo:
    basic_info = BasicInfo(**payload.model_dump())
    db.add(basic_info)
    db.commit()
    db.refresh(basic_info)
    return basic_info


@app.get("/api/basic-info/latest", response_model=BasicInfoResponse)
def get_latest_basic_info(db: Session = Depends(get_db)) -> BasicInfo:
    basic_info = _get_latest_basic_info(db)
    if not basic_info:
        raise HTTPException(status_code=404, detail="Basic info not found")
    return basic_info


@app.put("/api/basic-info/{basic_info_id}", response_model=BasicInfoResponse)
def update_basic_info(
    basic_info_id: uuid.UUID, payload: BasicInfoUpdate, db: Session = Depends(get_db)
) -> BasicInfo:
    basic_info = db.get(BasicInfo, basic_info_id)
    if not basic_info:
        raise HTTPException(status_code=404, detail="Basic info not found")

    for field, value in payload.model_dump().items():
        setattr(basic_info, field, value)

    db.commit()
    db.refresh(basic_info)
    return basic_info


@app.post("/api/resumes", response_model=ResumeResponse, status_code=201)
def create_resume(payload: ResumeCreate, db: Session = Depends(get_db)) -> Resume:
    resume = Resume(**payload.model_dump())
    db.add(resume)
    db.commit()
    db.refresh(resume)
    return resume


@app.get("/api/resumes/{resume_id}", response_model=ResumeResponse)
def get_resume(resume_id: uuid.UUID, db: Session = Depends(get_db)) -> Resume:
    resume = db.get(Resume, resume_id)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    return resume


@app.put("/api/resumes/{resume_id}", response_model=ResumeResponse)
def update_resume(
    resume_id: uuid.UUID, payload: ResumeUpdate, db: Session = Depends(get_db)
) -> Resume:
    resume = db.get(Resume, resume_id)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    for field, value in payload.model_dump().items():
        setattr(resume, field, value)

    db.commit()
    db.refresh(resume)
    return resume


@app.get("/api/resumes/{resume_id}/pdf")
def download_resume_pdf(resume_id: uuid.UUID, db: Session = Depends(get_db)) -> StreamingResponse:
    resume = db.get(Resume, resume_id)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    basic_info = _get_latest_basic_info(db)

    payload = {
        "full_name": basic_info.full_name if basic_info else "",
        "record_date": basic_info.record_date if basic_info else "",
        "qualifications": basic_info.qualifications if basic_info else [],
        "self_pr": resume.self_pr,
        "experiences": resume.experiences,
    }
    pdf_bytes = build_resume_pdf(payload)

    headers = {
        "Content-Disposition": f'attachment; filename="career-resume-{resume.id}.pdf"',
    }
    return StreamingResponse(io.BytesIO(pdf_bytes), media_type="application/pdf", headers=headers)


@app.post("/api/rirekisho", response_model=RirekishoResponse, status_code=201)
def create_rirekisho(payload: RirekishoCreate, db: Session = Depends(get_db)) -> Rirekisho:
    rirekisho = Rirekisho(**payload.model_dump())
    db.add(rirekisho)
    db.commit()
    db.refresh(rirekisho)
    return rirekisho


@app.get("/api/rirekisho/{rirekisho_id}", response_model=RirekishoResponse)
def get_rirekisho(rirekisho_id: uuid.UUID, db: Session = Depends(get_db)) -> Rirekisho:
    rirekisho = db.get(Rirekisho, rirekisho_id)
    if not rirekisho:
        raise HTTPException(status_code=404, detail="Rirekisho not found")
    return rirekisho


@app.put("/api/rirekisho/{rirekisho_id}", response_model=RirekishoResponse)
def update_rirekisho(
    rirekisho_id: uuid.UUID, payload: RirekishoUpdate, db: Session = Depends(get_db)
) -> Rirekisho:
    rirekisho = db.get(Rirekisho, rirekisho_id)
    if not rirekisho:
        raise HTTPException(status_code=404, detail="Rirekisho not found")

    for field, value in payload.model_dump().items():
        setattr(rirekisho, field, value)

    db.commit()
    db.refresh(rirekisho)
    return rirekisho


@app.get("/api/rirekisho/{rirekisho_id}/pdf")
def download_rirekisho_pdf(rirekisho_id: uuid.UUID, db: Session = Depends(get_db)) -> StreamingResponse:
    rirekisho = db.get(Rirekisho, rirekisho_id)
    if not rirekisho:
        raise HTTPException(status_code=404, detail="Rirekisho not found")

    basic_info = _get_latest_basic_info(db)

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
    pdf_bytes = build_rirekisho_pdf(payload)

    headers = {
        "Content-Disposition": f'attachment; filename="rirekisho-{rirekisho.id}.pdf"',
    }
    return StreamingResponse(io.BytesIO(pdf_bytes), media_type="application/pdf", headers=headers)
