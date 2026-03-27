from sqlalchemy.orm import selectinload

from ..core.date_utils import parse_iso_date
from ..models import BasicInfo, BasicInfoQualification
from ..services.sort_utils import sort_by_date_desc
from .base import SingleUserDocumentRepository


class BasicInfoRepository(SingleUserDocumentRepository):
    _model = BasicInfo
    _loader_options = (selectinload(BasicInfo.qualification_rows),)

    def _apply_payload(self, entity: BasicInfo, payload: dict[str, object]) -> None:
        entity.full_name = payload["full_name"]
        entity.name_furigana = payload["name_furigana"]
        entity.record_date_value = parse_iso_date(payload["record_date"])
        sorted_qualifications = sort_by_date_desc(
            payload.get("qualifications", []),
            date_key="acquired_date",
        )
        entity.qualification_rows = [
            BasicInfoQualification(
                sort_order=index,
                acquired_date_value=parse_iso_date(item["acquired_date"]),
                name=item["name"],
            )
            for index, item in enumerate(sorted_qualifications)
        ]
