import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..models import User
from ..repositories import BasicInfoRepository
from ..schemas import BasicInfoCreate, BasicInfoResponse, BasicInfoUpdate

router = APIRouter(prefix="/api/basic-info", tags=["basic-info"])


@router.post("", response_model=BasicInfoResponse, status_code=201)
def create_basic_info(
    payload: BasicInfoCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BasicInfoResponse:
    repository = BasicInfoRepository(db, current_user.id)
    return repository.create(payload.model_dump())


@router.get("/latest", response_model=BasicInfoResponse)
def get_latest_basic_info(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BasicInfoResponse:
    repository = BasicInfoRepository(db, current_user.id)
    basic_info = repository.get_latest()
    if not basic_info:
        raise HTTPException(status_code=404, detail="Basic info not found")
    return basic_info


@router.put("/{basic_info_id}", response_model=BasicInfoResponse)
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
