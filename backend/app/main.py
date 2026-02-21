import io
import os
import uuid

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from .models import Resume
from .schemas import ResumeCreate, ResumeResponse, ResumeUpdate
from .services.pdf_generator import build_resume_pdf

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


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


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

    payload = {
        "full_name": resume.full_name,
        "email": resume.email,
        "phone": resume.phone,
        "summary": resume.summary,
        "experiences": resume.experiences,
        "educations": resume.educations,
        "skills": resume.skills,
    }
    pdf_bytes = build_resume_pdf(payload)

    headers = {
        "Content-Disposition": f'attachment; filename="resume-{resume.id}.pdf"',
    }
    return StreamingResponse(io.BytesIO(pdf_bytes), media_type="application/pdf", headers=headers)
