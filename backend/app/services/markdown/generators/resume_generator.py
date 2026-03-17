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

            # clients → projects（後方互換: clients がなく projects がある場合）
            clients = exp.get("clients", [])
            if not clients and exp.get("projects"):
                clients = [{"name": "", "projects": exp["projects"]}]
            for client in clients:
                client_name = client.get("name", "")
                if client_name:
                    lines.append(f"#### {client_name}")
                    lines.append("")
                projects = client.get("projects", [])
                for proj in projects:
                    name = proj.get("name", "")
                    if name:
                        lines.append(f"##### {name}")
                        lines.append("")
                    proj_start = proj.get("start_date", "")
                    proj_end = proj.get("end_date", "")
                    proj_is_current = proj.get("is_current", False)
                    if proj_start:
                        proj_period = format_period(proj_start, proj_end, proj_is_current)
                        lines.append(field_line("期間", proj_period))
                    role = proj.get("role", "")
                    if role:
                        lines.append(field_line("担当", role))
                    desc = proj.get("description", "")
                    if desc:
                        lines.append(field_line("業務内容", desc))
                    challenge = proj.get("challenge", "")
                    if challenge:
                        lines.append(field_line("課題", challenge))
                    action = proj.get("action", "")
                    if action:
                        lines.append(field_line("行動", action))
                    result = proj.get("result", "")
                    if result:
                        lines.append(field_line("成果", result))
                    scale = proj.get("scale", "")
                    if scale:
                        lines.append(field_line("規模", f"{scale}名"))
                    stacks = proj.get("technology_stacks", [])
                    if stacks:
                        cat_labels = {
                            "language": "言語", "framework": "FW",
                            "os": "OS", "db": "DB",
                            "cloud_resource": "NW", "dev_tool": "Tool",
                        }
                        grouped: dict[str, list[str]] = {}
                        for st in stacks:
                            cat = st.get("category", "")
                            if cat not in grouped:
                                grouped[cat] = []
                            grouped[cat].append(st.get("name", ""))
                        parts = [
                            f"{cat_labels.get(c, c)}: {', '.join(ns)}"
                            for c, ns in grouped.items()
                        ]
                        lines.append(field_line("技術スタック", " / ".join(parts)))
                    lines.append("")

    self_pr = payload.get("self_pr", "")
    if self_pr:
        lines.append(tpl.SECTION_SELF_PR)
        lines.append("")
        lines.append(self_pr)
        lines.append("")

    return "\n".join(lines)
