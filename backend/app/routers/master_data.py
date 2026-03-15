from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import verify_admin_token
from ..repositories import MasterDataRepository
from ..schemas import MasterDataCreate, MasterDataItem, MasterDataUpdate

router = APIRouter(prefix="/api/master-data", tags=["master-data"])


@router.get("/{category}", response_model=list[MasterDataItem])
def list_master_data(category: str, db: Session = Depends(get_db)):
    """カテゴリ別マスタデータ一覧を取得する（認証不要）。"""
    repo = MasterDataRepository(db)
    return repo.list_by_category(category)


@router.post("", response_model=MasterDataItem, status_code=status.HTTP_201_CREATED)
def create_master_data(
    body: MasterDataCreate,
    db: Session = Depends(get_db),
    _: None = Depends(verify_admin_token),
):
    """マスタデータを新規作成する（admin認証必須）。"""
    repo = MasterDataRepository(db)
    return repo.create(body.category, body.name, body.sort_order)


@router.put("/{item_id}", response_model=MasterDataItem)
def update_master_data(
    item_id: str,
    body: MasterDataUpdate,
    db: Session = Depends(get_db),
    _: None = Depends(verify_admin_token),
):
    """マスタデータを更新する（admin認証必須）。"""
    repo = MasterDataRepository(db)
    updated = repo.update(item_id, body.name, body.sort_order)
    if not updated:
        raise HTTPException(status_code=404, detail="マスタデータが見つかりません")
    return updated


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_master_data(
    item_id: str,
    db: Session = Depends(get_db),
    _: None = Depends(verify_admin_token),
):
    """マスタデータを削除する（admin認証必須）。"""
    repo = MasterDataRepository(db)
    if not repo.delete(item_id):
        raise HTTPException(status_code=404, detail="マスタデータが見つかりません")
