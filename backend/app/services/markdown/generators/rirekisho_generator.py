from typing import Any

from ..templates import rirekisho_template as tpl
from ..utils.markdown_utils import field_line


def _a(obj, key, default=""):
    """dict / ORM オブジェクト両対応の属性アクセス"""
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def build_rirekisho_markdown(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append(tpl.TITLE)
    lines.append("")

    full_name = payload.get("full_name", "")
    name_furigana = payload.get("name_furigana", "")
    if name_furigana:
        lines.append(field_line("ふりがな", name_furigana))
    if full_name:
        lines.append(field_line("氏名", full_name))
    gender_raw = payload.get("gender", "")
    gender_labels = {"male": "男", "female": "女"}
    gender_text = gender_labels.get(gender_raw, "")
    if gender_text:
        lines.append(field_line("性別", gender_text))
    record_date = payload.get("record_date", "")
    if record_date:
        lines.append(field_line("記載日", record_date))
    lines.append("")

    prefecture = payload.get("prefecture", "")
    address = payload.get("address", "")
    address_furigana = payload.get("address_furigana", "")
    if address_furigana:
        lines.append(field_line("住所ふりがな", address_furigana))
    if prefecture or address:
        lines.append(field_line("住所", f"{prefecture}{address}"))
    lines.append("")

    lines.append(tpl.SECTION_CONTACT)
    lines.append("")
    phone = payload.get("phone", "")
    if phone:
        lines.append(field_line("電話", phone))
    email = payload.get("email", "")
    if email:
        lines.append(field_line("メール", email))
    lines.append("")

    educations = payload.get("educations", [])
    if educations:
        lines.append(tpl.SECTION_EDUCATION)
        lines.append("")
        for edu in educations:
            lines.append(f"- {_a(edu, 'date')} {_a(edu, 'name')}")
        lines.append("")

    work_histories = payload.get("work_histories", [])
    if work_histories:
        lines.append(tpl.SECTION_WORK_HISTORY)
        lines.append("")
        for wh in work_histories:
            lines.append(f"- {_a(wh, 'date')} {_a(wh, 'name')}")
        lines.append("")

    qualifications = payload.get("qualifications", [])
    if qualifications:
        lines.append(tpl.SECTION_QUALIFICATIONS)
        lines.append("")
        for q in qualifications:
            name = _a(q, "name")
            date = _a(q, "acquired_date")
            lines.append(f"- {name} ({date}取得)")
        lines.append("")

    motivation = payload.get("motivation", "")
    if motivation:
        lines.append(tpl.SECTION_MOTIVATION)
        lines.append("")
        lines.append(motivation)
        lines.append("")

    personal_preferences = payload.get("personal_preferences", "")
    if personal_preferences:
        lines.append(tpl.SECTION_PERSONAL_PREFERENCES)
        lines.append("")
        lines.append(personal_preferences)
        lines.append("")

    return "\n".join(lines)
