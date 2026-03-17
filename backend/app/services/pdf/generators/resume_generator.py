from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from ..utils.pdf_utils import (
    FONT_NAME,
    HEADER_BG,
    MARGIN,
    PAGE_W,
    TABLE_BORDER,
    TABLE_INNER,
    escape,
    format_period,
    nl2br,
    register_font,
    styles,
)


def _build_project_table(project: dict, s: dict) -> list:
    """Build table rows for a single project."""
    elements = []

    proj_name = escape(project.get("name", ""))
    proj_start = project.get("start_date", "")
    proj_end = project.get("end_date", "")
    proj_is_current = project.get("is_current", False)
    proj_period = format_period(proj_start, proj_end, proj_is_current) if proj_start else ""
    role = escape(project.get("role", ""))
    header_parts = []
    if proj_name:
        header_parts.append(proj_name)
    if proj_period:
        header_parts.append(proj_period)
    if role:
        header_parts.append(f"役割: {role}")
    if header_parts:
        elements.append(Paragraph(
            f"<b>{' ／ '.join(header_parts)}</b>",
            s["project_header"],
        ))

    # Left column: description + achievements
    left_parts = []
    if project.get("description"):
        left_parts.append(f"<b>【業務内容】</b><br/>{nl2br(project['description'])}")
    if project.get("achievements"):
        left_parts.append(f"<b>【実績・取り組み】</b><br/>{nl2br(project['achievements'])}")
    left_content = "<br/><br/>".join(left_parts) if left_parts else "-"

    # Right column: tech stacks
    tech_stacks = project.get("technology_stacks", [])
    grouped: dict[str, list[str]] = {}
    for stack in tech_stacks:
        cat = stack.get("category", "")
        name = stack.get("name", "")
        if cat not in grouped:
            grouped[cat] = []
        grouped[cat].append(name)

    right_parts = []
    for cat, names in grouped.items():
        right_parts.append(f"<b>【{escape(cat)}】</b><br/>{escape(', '.join(names))}")
    right_content = "<br/>".join(right_parts) if right_parts else "-"

    scale_raw = project.get("scale", "")
    scale = f"{escape(scale_raw)}名" if scale_raw else "-"

    col_widths = [105 * mm, 45 * mm, 25 * mm]
    header_data = [[
        Paragraph("<b>業務内容</b>", s["body_small"]),
        Paragraph("<b>開発環境</b>", s["body_small"]),
        Paragraph("<b>規模</b>", s["body_small"]),
    ]]
    body_data = [[
        Paragraph(left_content, s["body_small"]),
        Paragraph(right_content, s["body_small"]),
        Paragraph(scale, s["body_small"]),
    ]]

    t = Table(header_data + body_data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
        ("FONTNAME", (0, 0), (-1, -1), FONT_NAME),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.5, TABLE_BORDER),
        ("INNERGRID", (0, 1), (-1, -1), 0.3, TABLE_INNER),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(t)
    return elements


def _add_page_number(canvas_obj, doc):
    register_font()
    canvas_obj.saveState()
    canvas_obj.setFont(FONT_NAME, 8)
    canvas_obj.drawCentredString(PAGE_W / 2, 10 * mm, f"{canvas_obj.getPageNumber()}")
    canvas_obj.restoreState()


def build_resume_pdf(resume: dict) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN, bottomMargin=MARGIN,
    )

    s = styles()
    elements = []

    # Title
    elements.append(Paragraph("職 務 経 歴 書", s["title"]))

    # Date and Name
    record_date = resume.get("record_date") or ""
    if record_date and "-" in record_date:
        parts = record_date.split("-")
        if len(parts) >= 2:
            record_date = f"{parts[0]} 年 {parts[1].lstrip('0')} 月"
        if len(parts) == 3:
            record_date += f" {parts[2].lstrip('0')} 日"
    elements.append(Paragraph(f"{escape(record_date)}現在", s["date"]))
    full_name = resume.get("full_name") or ""
    elements.append(Paragraph(f"氏名　{escape(full_name)}", s["name"]))

    # 職務要約
    elements.append(Paragraph("■職務要約", s["section_header"]))
    elements.append(Paragraph(nl2br(resume.get("career_summary", "")), s["body"]))

    # 職務経歴
    elements.append(Paragraph("■職務経歴", s["section_header"]))
    experiences = resume.get("experiences", [])
    if not experiences:
        elements.append(Paragraph("-", s["body"]))
    else:
        for exp in experiences:
            period = format_period(
                exp["start_date"], exp.get("end_date"), exp.get("is_current", False)
            )
            company = escape(exp["company"])

            # Company info
            biz = escape(exp.get("business_description") or exp.get("title", ""))
            capital_raw = exp.get("capital", "")
            emp_raw = exp.get("employee_count", "")
            capital = f"{escape(capital_raw)}千万円" if capital_raw else ""
            emp = f"{escape(emp_raw)}名" if emp_raw else ""
            info_parts = [f"事業内容：{biz}"]
            if capital:
                info_parts.append(f"資本金：{capital}")
            if emp:
                info_parts.append(f"従業員数：{emp}")

            # Build inner content for this company
            inner = []

            # clients → projects（後方互換: clients がなく projects がある場合はそのまま描画）
            clients = exp.get("clients", [])
            if not clients and exp.get("projects"):
                clients = [{"name": "", "projects": exp["projects"]}]
            for client in clients:
                client_name = escape(client.get("name", ""))
                if client_name:
                    inner.append(Paragraph(
                        f"<b>▸ {client_name}</b>",
                        s["company_header"],
                    ))
                    inner.append(Spacer(1, 1 * mm))
                projects = client.get("projects", [])
                for proj in projects:
                    proj_elements = _build_project_table(proj, s)
                    inner.extend(proj_elements)
                    inner.append(Spacer(1, 2 * mm))

            # Wrap company in a bordered table
            content_width = PAGE_W - 2 * MARGIN
            company_table = Table(
                [
                    [Paragraph(f"<b>{period}　{company}</b>", s["company_header"])],
                    [Paragraph("　".join(info_parts), s["body_small"])],
                    [inner],
                ],
                colWidths=[content_width],
            )
            company_table.setStyle(TableStyle([
                ("BOX", (0, 0), (-1, -1), 0.5, TABLE_BORDER),
                ("BACKGROUND", (0, 0), (0, 0), HEADER_BG),
                ("BACKGROUND", (0, 1), (0, 1), HEADER_BG),
                ("LINEBELOW", (0, 0), (-1, 0), 0.3, TABLE_INNER),
                ("LINEBELOW", (0, 1), (-1, 1), 0.3, TABLE_INNER),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ]))
            elements.append(company_table)
            elements.append(Spacer(1, 3 * mm))

    # 資格
    elements.append(Paragraph("■資格", s["section_header"]))
    qualifications = resume.get("qualifications", [])
    if not qualifications:
        elements.append(Paragraph("-", s["body"]))
    else:
        qual_data = []
        for q in qualifications:
            name = escape(q.get("name", ""))
            raw_date = q.get("acquired_date", "")
            if raw_date and "-" in raw_date:
                dp = raw_date.split("-")
                if len(dp) == 3:
                    date_str = f"{dp[0]}年{dp[1].lstrip('0')}月{dp[2].lstrip('0')}日取得"
                elif len(dp) == 2:
                    date_str = f"{dp[0]}年{dp[1].lstrip('0')}月取得"
                else:
                    date_str = f"{escape(raw_date)}取得"
            else:
                date_str = f"{escape(raw_date)}取得" if raw_date else ""
            qual_data.append([
                Paragraph(name, s["qual"]),
                Paragraph(date_str, s["qual"]),
            ])
        qual_table = Table(qual_data, colWidths=[110 * mm, 65 * mm])
        qual_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.5, TABLE_BORDER),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ]))
        elements.append(qual_table)

    # 自己PR
    elements.append(Paragraph("■自己PR", s["section_header"]))
    elements.append(Paragraph(nl2br(resume.get("self_pr", "")), s["body"]))

    doc.build(elements, onFirstPage=_add_page_number, onLaterPages=_add_page_number)
    buffer.seek(0)
    return buffer.getvalue()
