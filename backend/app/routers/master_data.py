from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import verify_admin_token
from ..repositories import MPrefectureRepository, MQualificationRepository, MTechnologyStackRepository
from ..schemas import (
    MasterItem,
    MasterItemCreate,
    MasterItemUpdate,
    TechStackMasterCreate,
    TechStackMasterItem,
    TechStackMasterUpdate,
)

router = APIRouter(prefix="/api/master-data", tags=["master-data"])


# --- 資格マスタ ---

@router.get("/qualification", response_model=list[MasterItem])
def list_qualifications(db: Session = Depends(get_db)):
    """資格マスタ一覧を取得する（認証不要）。"""
    return MQualificationRepository(db).list_all()


@router.post("/qualification", response_model=MasterItem, status_code=status.HTTP_201_CREATED)
def create_qualification(
    body: MasterItemCreate,
    db: Session = Depends(get_db),
    _: None = Depends(verify_admin_token),
):
    """資格マスタを新規作成する（admin認証必須）。"""
    return MQualificationRepository(db).create(body.name, body.sort_order)


@router.put("/qualification/{item_id}", response_model=MasterItem)
def update_qualification(
    item_id: str,
    body: MasterItemUpdate,
    db: Session = Depends(get_db),
    _: None = Depends(verify_admin_token),
):
    """資格マスタを更新する（admin認証必須）。"""
    updated = MQualificationRepository(db).update(item_id, body.name, body.sort_order)
    if not updated:
        raise HTTPException(status_code=404, detail="資格マスタが見つかりません")
    return updated


@router.delete("/qualification/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_qualification(
    item_id: str,
    db: Session = Depends(get_db),
    _: None = Depends(verify_admin_token),
):
    """資格マスタを削除する（admin認証必須）。"""
    if not MQualificationRepository(db).delete(item_id):
        raise HTTPException(status_code=404, detail="資格マスタが見つかりません")


# --- 技術スタックマスタ ---

@router.get("/technology-stack", response_model=list[TechStackMasterItem])
def list_technology_stacks(db: Session = Depends(get_db)):
    """技術スタックマスタ一覧を取得する（認証不要）。"""
    return MTechnologyStackRepository(db).list_all()


@router.post("/technology-stack", response_model=TechStackMasterItem, status_code=status.HTTP_201_CREATED)
def create_technology_stack(
    body: TechStackMasterCreate,
    db: Session = Depends(get_db),
    _: None = Depends(verify_admin_token),
):
    """技術スタックマスタを新規作成する（admin認証必須）。"""
    return MTechnologyStackRepository(db).create(body.category, body.name, body.sort_order)


@router.put("/technology-stack/{item_id}", response_model=TechStackMasterItem)
def update_technology_stack(
    item_id: str,
    body: TechStackMasterUpdate,
    db: Session = Depends(get_db),
    _: None = Depends(verify_admin_token),
):
    """技術スタックマスタを更新する（admin認証必須）。"""
    updated = MTechnologyStackRepository(db).update(item_id, body.name, body.sort_order, body.category)
    if not updated:
        raise HTTPException(status_code=404, detail="技術スタックマスタが見つかりません")
    return updated


@router.delete("/technology-stack/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_technology_stack(
    item_id: str,
    db: Session = Depends(get_db),
    _: None = Depends(verify_admin_token),
):
    """技術スタックマスタを削除する（admin認証必須）。"""
    if not MTechnologyStackRepository(db).delete(item_id):
        raise HTTPException(status_code=404, detail="技術スタックマスタが見つかりません")


# --- 都道府県マスタ ---

@router.get("/prefecture", response_model=list[MasterItem])
def list_prefectures(db: Session = Depends(get_db)):
    """都道府県マスタ一覧を取得する（認証不要）。"""
    return MPrefectureRepository(db).list_all()


@router.post("/prefecture", response_model=MasterItem, status_code=status.HTTP_201_CREATED)
def create_prefecture(
    body: MasterItemCreate,
    db: Session = Depends(get_db),
    _: None = Depends(verify_admin_token),
):
    """都道府県マスタを新規作成する（admin認証必須）。"""
    return MPrefectureRepository(db).create(body.name, body.sort_order)


@router.put("/prefecture/{item_id}", response_model=MasterItem)
def update_prefecture(
    item_id: str,
    body: MasterItemUpdate,
    db: Session = Depends(get_db),
    _: None = Depends(verify_admin_token),
):
    """都道府県マスタを更新する（admin認証必須）。"""
    updated = MPrefectureRepository(db).update(item_id, body.name, body.sort_order)
    if not updated:
        raise HTTPException(status_code=404, detail="都道府県マスタが見つかりません")
    return updated


@router.delete("/prefecture/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_prefecture(
    item_id: str,
    db: Session = Depends(get_db),
    _: None = Depends(verify_admin_token),
):
    """都道府県マスタを削除する（admin認証必須）。"""
    if not MPrefectureRepository(db).delete(item_id):
        raise HTTPException(status_code=404, detail="都道府県マスタが見つかりません")
