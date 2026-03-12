from typing import Any

from ..templates import resume_template as tpl
from ..utils.markdown_utils import field_line, format_period


def build_resume_markdown(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append(tpl.TITLE)
    lines.append("")

    full_name = payload.get("full_name", "")
    record_date = payload.get("record_date", "")
    if full_name:
        lines.append(field_line("氏名", full_name))
    if record_date:
        lines.append(field_line("記載日", record_date))
    lines.append("")

    qualifications = payload.get("qualifications", [])
    if qualifications:
        lines.append(tpl.SECTION_QUALIFICATIONS)
        lines.append("")
        for q in qualifications:
            lines.append(f"- {q.get('name', '')} ({q.get('acquired_date', '')}取得)")
        lines.append("")

    career_summary = payload.get("career_summary", "")
    if career_summary:
        lines.append(tpl.SECTION_CAREER_SUMMARY)
        lines.append("")
        lines.append(career_summary)
        lines.append("")

    experiences = payload.get("experiences", [])
    if experiences:
        lines.append(tpl.SECTION_EXPERIENCES)
        lines.append("")
        for exp in experiences:
            company = exp.get("company", "")
            start = exp.get("start_date", "")
            end = exp.get("end_date", "")
            is_current = exp.get("is_current", False)
            period = format_period(start, end, is_current)
            lines.append(f"### {company}")
            lines.append("")
            lines.append(field_line("期間", period))
            biz = exp.get("business_description", "")
            if biz:
                lines.append(field_line("事業内容", biz))
            emp = exp.get("employee_count", "")
            if emp:
                lines.append(field_line("従業員数", f"{emp}名"))
            cap = exp.get("capital", "")
            if cap:
                lines.append(field_line("資本金", f"{cap}千万円"))
            lines.append("")

            projects = exp.get("projects", [])
            for proj in projects:
                name = proj.get("name", "")
                if name:
                    lines.append(f"#### {name}")
                    lines.append("")
                role = proj.get("role", "")
                if role:
                    lines.append(field_line("担当", role))
                desc = proj.get("description", "")
                if desc:
                    lines.append(field_line("業務内容", desc))
                achievements = proj.get("achievements", "")
                if achievements:
                    lines.append(field_line("実績", achievements))
                scale = proj.get("scale", "")
                if scale:
                    lines.append(field_line("規模", f"{scale}名"))
                stacks = proj.get("technology_stacks", [])
                if stacks:
                    tech_str = ", ".join(s.get("name", "") for s in stacks)
                    lines.append(field_line("技術スタック", tech_str))
                lines.append("")

    self_pr = payload.get("self_pr", "")
    if self_pr:
        lines.append(tpl.SECTION_SELF_PR)
        lines.append("")
        lines.append(self_pr)
        lines.append("")

    return "\n".join(lines)
