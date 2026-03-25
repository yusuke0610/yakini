import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..messages import get_error, get_success
from ..models import User
from ..repositories import BasicInfoRepository, RirekishoRepository
from ..schemas import RirekishoCreate, RirekishoResponse, RirekishoUpdate
from ..services.markdown.generators.rirekisho_generator import (
    build_rirekisho_markdown,
)
from ..services.pdf.generators.rirekisho_generator import build_rirekisho_pdf
from .download_utils import stream_markdown, stream_pdf

router = APIRouter(prefix="/api/rirekisho", tags=["rirekisho"])


@router.post("", response_model=RirekishoResponse, status_code=201)
def create_rirekisho(
    payload: RirekishoCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RirekishoResponse:
    repository = RirekishoRepository(db, current_user.id)
    try:
        return repository.create(payload.model_dump())
    except ValueError as exc:
        raise HTTPException(
            status_code=409,
            detail=get_error(str(exc), document="履歴書"),
        ) from exc


@router.get("/latest", response_model=RirekishoResponse)
def get_latest_rirekisho(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RirekishoResponse:
    repository = RirekishoRepository(db, current_user.id)
    rirekisho = repository.get_latest()
    if not rirekisho:
        raise HTTPException(
            status_code=404,
            detail=get_error("document.not_found", document="履歴書"),
        )
    return rirekisho


@router.delete("")
def delete_rirekisho(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    repository = RirekishoRepository(db, current_user.id)
    if not repository.delete():
        raise HTTPException(
            status_code=404,
            detail=get_error("document.not_found", document="履歴書"),
        )
    return {"message": get_success("document.deleted", document="履歴書")}


@router.get("/{rirekisho_id}", response_model=RirekishoResponse)
def get_rirekisho(
    rirekisho_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RirekishoResponse:
    repository = RirekishoRepository(db, current_user.id)
    rirekisho = repository.get_by_id(str(rirekisho_id))
    if not rirekisho:
        raise HTTPException(
            status_code=404,
            detail=get_error("document.not_found", document="履歴書"),
        )
    return rirekisho


@router.put("/{rirekisho_id}", response_model=RirekishoResponse)
def update_rirekisho(
    rirekisho_id: uuid.UUID,
    payload: RirekishoUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RirekishoResponse:
    repository = RirekishoRepository(db, current_user.id)
    rirekisho = repository.get_by_id(str(rirekisho_id))
    if not rirekisho:
        raise HTTPException(
            status_code=404,
            detail=get_error("document.not_found", document="履歴書"),
        )

    return repository.update(rirekisho, payload.model_dump())


@router.get("/{rirekisho_id}/pdf")
def download_rirekisho_pdf(
    rirekisho_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    rirekisho_repository = RirekishoRepository(db, current_user.id)
    basic_info_repository = BasicInfoRepository(db, current_user.id)

    rirekisho = rirekisho_repository.get_by_id(str(rirekisho_id))
    if not rirekisho:
        raise HTTPException(
            status_code=404,
            detail=get_error("document.not_found", document="履歴書"),
        )

    basic_info = basic_info_repository.get_latest()

    payload = {
        "full_name": basic_info.full_name if basic_info else "",
        "record_date": basic_info.record_date if basic_info else "",
        "qualifications": basic_info.qualifications if basic_info else [],
        "name_furigana": basic_info.name_furigana if basic_info else "",
        "gender": rirekisho.gender,
        "birthday": rirekisho.birthday,
        "postal_code": rirekisho.postal_code,
        "prefecture": rirekisho.prefecture,
        "address": rirekisho.address,
        "address_furigana": rirekisho.address_furigana,
        "email": rirekisho.email,
        "phone": rirekisho.phone,
        "motivation": rirekisho.motivation,
        "personal_preferences": rirekisho.personal_preferences,
        "photo": rirekisho.photo,
        "educations": rirekisho.educations,
        "work_histories": rirekisho.work_histories,
    }
    pdf_bytes = build_rirekisho_pdf(payload)
    return stream_pdf(pdf_bytes, f"rirekisho-{rirekisho.id}.pdf")


@router.get("/{rirekisho_id}/markdown")
def download_rirekisho_markdown(
    rirekisho_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    rirekisho_repository = RirekishoRepository(db, current_user.id)
    basic_info_repository = BasicInfoRepository(db, current_user.id)

    rirekisho = rirekisho_repository.get_by_id(str(rirekisho_id))
    if not rirekisho:
        raise HTTPException(
            status_code=404,
            detail=get_error("document.not_found", document="履歴書"),
        )

    basic_info = basic_info_repository.get_latest()

    payload = {
        "full_name": basic_info.full_name if basic_info else "",
        "record_date": basic_info.record_date if basic_info else "",
        "qualifications": basic_info.qualifications if basic_info else [],
        "name_furigana": basic_info.name_furigana if basic_info else "",
        "gender": rirekisho.gender,
        "birthday": rirekisho.birthday,
        "postal_code": rirekisho.postal_code,
        "prefecture": rirekisho.prefecture,
        "address": rirekisho.address,
        "address_furigana": rirekisho.address_furigana,
        "email": rirekisho.email,
        "phone": rirekisho.phone,
        "motivation": rirekisho.motivation,
        "personal_preferences": rirekisho.personal_preferences,
        "educations": rirekisho.educations,
        "work_histories": rirekisho.work_histories,
    }
    md_text = build_rirekisho_markdown(payload)
    return stream_markdown(md_text, f"rirekisho-{rirekisho.id}.md")
