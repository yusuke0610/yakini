from typing import Any

from ..templates import rirekisho_template as tpl
from ..utils.markdown_utils import field_line


def build_rirekisho_markdown(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append(tpl.TITLE)
    lines.append("")

    full_name = payload.get("full_name", "")
    if full_name:
        lines.append(field_line("氏名", full_name))
    record_date = payload.get("record_date", "")
    if record_date:
        lines.append(field_line("記載日", record_date))
    lines.append("")

    lines.append(tpl.SECTION_CONTACT)
    lines.append("")
    postal = payload.get("postal_code", "")
    if postal:
        lines.append(field_line("郵便番号", postal))
    prefecture = payload.get("prefecture", "")
    address = payload.get("address", "")
    if prefecture or address:
        lines.append(field_line("住所", f"{prefecture}{address}"))
    email = payload.get("email", "")
    if email:
        lines.append(field_line("メール", email))
    phone = payload.get("phone", "")
    if phone:
        lines.append(field_line("電話", phone))
    lines.append("")

    educations = payload.get("educations", [])
    if educations:
        lines.append(tpl.SECTION_EDUCATION)
        lines.append("")
        for edu in educations:
            lines.append(f"- {edu.get('date', '')} {edu.get('name', '')}")
        lines.append("")

    work_histories = payload.get("work_histories", [])
    if work_histories:
        lines.append(tpl.SECTION_WORK_HISTORY)
        lines.append("")
        for wh in work_histories:
            lines.append(f"- {wh.get('date', '')} {wh.get('name', '')}")
        lines.append("")

    qualifications = payload.get("qualifications", [])
    if qualifications:
        lines.append(tpl.SECTION_QUALIFICATIONS)
        lines.append("")
        for q in qualifications:
            lines.append(f"- {q.get('name', '')} ({q.get('acquired_date', '')}取得)")
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
