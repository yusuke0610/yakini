from typing import Any


def build_resume_markdown(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# 職務経歴書")
    lines.append("")

    full_name = payload.get("full_name", "")
    record_date = payload.get("record_date", "")
    if full_name:
        lines.append(f"**氏名:** {full_name}")
    if record_date:
        lines.append(f"**記載日:** {record_date}")
    lines.append("")

    qualifications = payload.get("qualifications", [])
    if qualifications:
        lines.append("## 資格")
        lines.append("")
        for q in qualifications:
            lines.append(f"- {q.get('name', '')} ({q.get('acquired_date', '')}取得)")
        lines.append("")

    career_summary = payload.get("career_summary", "")
    if career_summary:
        lines.append("## 職務要約")
        lines.append("")
        lines.append(career_summary)
        lines.append("")

    experiences = payload.get("experiences", [])
    if experiences:
        lines.append("## 職務経歴")
        lines.append("")
        for exp in experiences:
            company = exp.get("company", "")
            start = exp.get("start_date", "")
            end = exp.get("end_date", "")
            is_current = exp.get("is_current", False)
            period = f"{start} - {'現在' if is_current else (end or '')}"
            lines.append(f"### {company}")
            lines.append("")
            lines.append(f"**期間:** {period}")
            biz = exp.get("business_description", "")
            if biz:
                lines.append(f"**事業内容:** {biz}")
            emp = exp.get("employee_count", "")
            if emp:
                lines.append(f"**従業員数:** {emp}名")
            cap = exp.get("capital", "")
            if cap:
                lines.append(f"**資本金:** {cap}千万円")
            lines.append("")

            projects = exp.get("projects", [])
            for proj in projects:
                name = proj.get("name", "")
                if name:
                    lines.append(f"#### {name}")
                    lines.append("")
                role = proj.get("role", "")
                if role:
                    lines.append(f"**担当:** {role}")
                desc = proj.get("description", "")
                if desc:
                    lines.append(f"**業務内容:** {desc}")
                achievements = proj.get("achievements", "")
                if achievements:
                    lines.append(f"**実績:** {achievements}")
                scale = proj.get("scale", "")
                if scale:
                    lines.append(f"**規模:** {scale}名")
                stacks = proj.get("technology_stacks", [])
                if stacks:
                    tech_str = ", ".join(s.get("name", "") for s in stacks)
                    lines.append(f"**技術スタック:** {tech_str}")
                lines.append("")

    self_pr = payload.get("self_pr", "")
    if self_pr:
        lines.append("## 自己PR")
        lines.append("")
        lines.append(self_pr)
        lines.append("")

    return "\n".join(lines)


def build_rirekisho_markdown(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# 履歴書")
    lines.append("")

    full_name = payload.get("full_name", "")
    if full_name:
        lines.append(f"**氏名:** {full_name}")
    record_date = payload.get("record_date", "")
    if record_date:
        lines.append(f"**記載日:** {record_date}")
    lines.append("")

    lines.append("## 連絡先")
    lines.append("")
    postal = payload.get("postal_code", "")
    if postal:
        lines.append(f"**郵便番号:** {postal}")
    prefecture = payload.get("prefecture", "")
    address = payload.get("address", "")
    if prefecture or address:
        lines.append(f"**住所:** {prefecture}{address}")
    email = payload.get("email", "")
    if email:
        lines.append(f"**メール:** {email}")
    phone = payload.get("phone", "")
    if phone:
        lines.append(f"**電話:** {phone}")
    lines.append("")

    educations = payload.get("educations", [])
    if educations:
        lines.append("## 学歴")
        lines.append("")
        for edu in educations:
            lines.append(f"- {edu.get('date', '')} {edu.get('name', '')}")
        lines.append("")

    work_histories = payload.get("work_histories", [])
    if work_histories:
        lines.append("## 職歴")
        lines.append("")
        for wh in work_histories:
            lines.append(f"- {wh.get('date', '')} {wh.get('name', '')}")
        lines.append("")

    qualifications = payload.get("qualifications", [])
    if qualifications:
        lines.append("## 資格")
        lines.append("")
        for q in qualifications:
            lines.append(f"- {q.get('name', '')} ({q.get('acquired_date', '')}取得)")
        lines.append("")

    motivation = payload.get("motivation", "")
    if motivation:
        lines.append("## 志望動機")
        lines.append("")
        lines.append(motivation)
        lines.append("")

    return "\n".join(lines)
