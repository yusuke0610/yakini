"""マスタデータの初期シードを投入するモジュール。

実データは ``backend/app/db/seeds/`` 配下の JSON ファイルに格納されている:
  - ``qualifications.json``: 資格マスタ
  - ``technology_stacks.json``: 技術スタックマスタ（カテゴリ付き）

本モジュールはローダーとシード投入オーケストレーションのみを担う。
"""

import json
from pathlib import Path

from sqlalchemy.orm import Session

from ..repositories import (
    MQualificationRepository,
    MTechnologyStackRepository,
)

_SEEDS_DIR = Path(__file__).parent / "seeds"


def _load_seed_file(filename: str) -> list[dict]:
    """``seeds/`` 配下の JSON ファイルを読み込んで dict のリストを返す。"""
    with (_SEEDS_DIR / filename).open(encoding="utf-8") as f:
        return json.load(f)


def seed_master_data(db: Session) -> None:
    """マスタデータの初期シードを投入する。各テーブルが空の場合のみ投入される。"""
    qualifications = _load_seed_file("qualifications.json")
    technology_stacks = _load_seed_file("technology_stacks.json")
    MQualificationRepository(db).seed_if_empty(qualifications)
    MTechnologyStackRepository(db).seed_if_empty(technology_stacks)
