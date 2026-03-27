import logging
from typing import Any

from sqlalchemy.orm import selectinload
from sqlalchemy.orm.attributes import set_committed_value

from ..core.date_utils import parse_iso_date, parse_year_month
from ..core.encryption import decrypt_field, encrypt_field
from ..models import Rirekisho, RirekishoEducation, RirekishoWorkHistory
from ..services.sort_utils import sort_by_date_asc
from .base import SingleUserDocumentRepository

_ENCRYPTED_RIREKISHO_FIELDS = {"email", "phone", "postal_code", "address"}


class RirekishoRepository(SingleUserDocumentRepository):
    """履歴書リポジトリ。個人情報フィールドの暗号化・復号を行う。"""

    _model = Rirekisho
    _loader_options = (
        selectinload(Rirekisho.education_rows),
        selectinload(Rirekisho.work_history_rows),
    )

    def _encrypt_value(self, field: str, value: str) -> str:
        if field in _ENCRYPTED_RIREKISHO_FIELDS:
            return encrypt_field(value)
        return value

    def _decrypt_rirekisho(self, rirekisho: Rirekisho) -> None:
        for field in _ENCRYPTED_RIREKISHO_FIELDS:
            value = getattr(rirekisho, field, None)
            if isinstance(value, str):
                try:
                    set_committed_value(rirekisho, field, decrypt_field(value))
                except Exception:
                    logging.warning(
                        "Failed to decrypt field %s, returning raw value",
                        field,
                        exc_info=True,
                    )

    def _apply_payload(self, entity: Rirekisho, payload: dict[str, Any]) -> None:
        entity.gender = payload["gender"]
        entity.birthday_value = parse_iso_date(payload["birthday"])
        entity.prefecture = payload["prefecture"]
        entity.postal_code = self._encrypt_value("postal_code", payload["postal_code"])
        entity.address = self._encrypt_value("address", payload["address"])
        entity.address_furigana = payload["address_furigana"]
        entity.email = self._encrypt_value("email", payload["email"])
        entity.phone = self._encrypt_value("phone", payload["phone"])
        entity.motivation = payload.get("motivation", "")
        entity.personal_preferences = payload.get("personal_preferences", "")
        entity.photo = payload.get("photo")
        sorted_educations = sort_by_date_asc(
            payload.get("educations", []), date_key="date",
        )
        entity.education_rows = [
            RirekishoEducation(
                sort_order=index,
                occurred_on_value=parse_year_month(item["date"]),
                name=item["name"],
            )
            for index, item in enumerate(sorted_educations)
        ]
        sorted_work_histories = sort_by_date_asc(
            payload.get("work_histories", []), date_key="date",
        )
        entity.work_history_rows = [
            RirekishoWorkHistory(
                sort_order=index,
                occurred_on_value=parse_year_month(item["date"]),
                name=item["name"],
            )
            for index, item in enumerate(sorted_work_histories)
        ]

    def create(self, payload: dict[str, Any]) -> Rirekisho:
        rirekisho = super().create(payload)
        self._decrypt_rirekisho(rirekisho)
        return rirekisho

    def get_current(self) -> Rirekisho | None:
        rirekisho = super().get_current()
        if rirekisho:
            self._decrypt_rirekisho(rirekisho)
        return rirekisho

    def get_by_id(self, entity_id: str) -> Rirekisho | None:
        rirekisho = super().get_by_id(entity_id)
        if rirekisho:
            self._decrypt_rirekisho(rirekisho)
        return rirekisho

    def update(self, entity: Any, payload: dict[str, Any]) -> Rirekisho:
        rirekisho = super().update(entity, payload)
        self._decrypt_rirekisho(rirekisho)
        return rirekisho
