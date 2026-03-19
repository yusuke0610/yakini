from typing import Callable

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import verify_admin_token
from ..repositories import (
    BaseMasterRepository,
    MPrefectureRepository,
    MQualificationRepository,
    MTechnologyStackRepository,
)
from ..schemas import (
    MasterItem,
    MasterItemCreate,
    MasterItemUpdate,
    TechStackMasterCreate,
    TechStackMasterItem,
    TechStackMasterUpdate,
)

router = APIRouter(prefix="/api/master-data", tags=["master-data"])


def _register_master_crud(
    path: str,
    repo_factory: Callable[[Session], BaseMasterRepository],
    label: str,
) -> None:
    """資格・都道府県など共通パターンのマスタ CRUD エンドポイントを一括登録する。"""

    @router.get(f"/{path}", response_model=list[MasterItem])
    def list_items(db: Session = Depends(get_db)):
        return repo_factory(db).list_all()

    @router.post(
        f"/{path}",
        response_model=MasterItem,
        status_code=status.HTTP_201_CREATED,
    )
    def create_item(
        body: MasterItemCreate,
        db: Session = Depends(get_db),
        _: None = Depends(verify_admin_token),
    ):
        return repo_factory(db).create(body.name, body.sort_order)

    @router.put(f"/{path}/{{item_id}}", response_model=MasterItem)
    def update_item(
        item_id: str,
        body: MasterItemUpdate,
        db: Session = Depends(get_db),
        _: None = Depends(verify_admin_token),
    ):
        updated = repo_factory(db).update(item_id, body.name, body.sort_order)
        if not updated:
            raise HTTPException(status_code=404, detail=f"{label}が見つかりません")
        return updated

    @router.delete(
        f"/{path}/{{item_id}}", status_code=status.HTTP_204_NO_CONTENT
    )
    def delete_item(
        item_id: str,
        db: Session = Depends(get_db),
        _: None = Depends(verify_admin_token),
    ):
        if not repo_factory(db).delete(item_id):
            raise HTTPException(status_code=404, detail=f"{label}が見つかりません")

    # FastAPI の OpenAPI ドキュメント用にユニークな関数名を設定
    list_items.__name__ = f"list_{path}s"
    create_item.__name__ = f"create_{path}"
    update_item.__name__ = f"update_{path}"
    delete_item.__name__ = f"delete_{path}"


_register_master_crud(
    "qualification", MQualificationRepository, "資格マスタ"
)
_register_master_crud("prefecture", MPrefectureRepository, "都道府県マスタ")


# --- 技術スタックマスタ（category フィールドがあるため個別定義） ---

@router.get("/technology-stack", response_model=list[TechStackMasterItem])
def list_technology_stacks(db: Session = Depends(get_db)):
    """技術スタックマスタ一覧を取得する（認証不要）。"""
    return MTechnologyStackRepository(db).list_all()


@router.post(
    "/technology-stack",
    response_model=TechStackMasterItem,
    status_code=status.HTTP_201_CREATED,
)
def create_technology_stack(
    body: TechStackMasterCreate,
    db: Session = Depends(get_db),
    _: None = Depends(verify_admin_token),
):
    """技術スタックマスタを新規作成する（admin認証必須）。"""
    return MTechnologyStackRepository(db).create(
        body.category, body.name, body.sort_order
    )


@router.put("/technology-stack/{item_id}", response_model=TechStackMasterItem)
def update_technology_stack(
    item_id: str,
    body: TechStackMasterUpdate,
    db: Session = Depends(get_db),
    _: None = Depends(verify_admin_token),
):
    """技術スタックマスタを更新する（admin認証必須）。"""
    updated = MTechnologyStackRepository(db).update(
        item_id, body.category, body.name, body.sort_order
    )
    if not updated:
        raise HTTPException(status_code=404, detail="技術スタックマスタが見つかりません")
    return updated


@router.delete(
    "/technology-stack/{item_id}", status_code=status.HTTP_204_NO_CONTENT
)
def delete_technology_stack(
    item_id: str,
    db: Session = Depends(get_db),
    _: None = Depends(verify_admin_token),
):
    """技術スタックマスタを削除する（admin認証必須）。"""
    if not MTechnologyStackRepository(db).delete(item_id):
        raise HTTPException(status_code=404, detail="技術スタックマスタが見つかりません")
