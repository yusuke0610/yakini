from io import BytesIO
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

_FONT_DIR = Path(__file__).resolve().parent.parent / "fonts"
_FONT_REGISTERED = False
FONT_NAME = "NotoSansJP"


def _register_font() -> None:
    global _FONT_REGISTERED
    if _FONT_REGISTERED:
        return
    font_path = _FONT_DIR / "NotoSansJP-Regular.ttf"
    if font_path.exists():
        pdfmetrics.registerFont(TTFont(FONT_NAME, str(font_path)))
    else:
        raise FileNotFoundError(f"Font not found: {font_path}")
    _FONT_REGISTERED = True


PAGE_W, PAGE_H = A4
MARGIN = 15 * mm

TABLE_BORDER = colors.HexColor("#666666")
TABLE_INNER = colors.HexColor("#999999")
HEADER_BG = colors.HexColor("#d6dce8")


def _styles() -> dict:
    _register_font()
    base = getSampleStyleSheet()

    s = {}
    s["title"] = ParagraphStyle(
        "title", parent=base["Normal"],
        fontName=FONT_NAME, fontSize=18, leading=24,
        alignment=TA_CENTER, spaceAfter=2 * mm,
    )
    s["date"] = ParagraphStyle(
        "date", parent=base["Normal"],
        fontName=FONT_NAME, fontSize=10, alignment=TA_RIGHT,
    )
    s["name"] = ParagraphStyle(
        "name", parent=base["Normal"],
        fontName=FONT_NAME, fontSize=11, alignment=TA_RIGHT,
        spaceAfter=4 * mm,
    )
    s["section_header"] = ParagraphStyle(
        "section_header", parent=base["Normal"],
        fontName=FONT_NAME, fontSize=12, leading=16,
        spaceBefore=4 * mm, spaceAfter=2 * mm,
    )
    s["body"] = ParagraphStyle(
        "body", parent=base["Normal"],
        fontName=FONT_NAME, fontSize=9, leading=14,
        spaceBefore=1 * mm,
    )
    s["body_small"] = ParagraphStyle(
        "body_small", parent=base["Normal"],
        fontName=FONT_NAME, fontSize=8, leading=12,
    )
    s["company_header"] = ParagraphStyle(
        "company_header", parent=base["Normal"],
        fontName=FONT_NAME, fontSize=10, leading=14,
        spaceBefore=3 * mm, spaceAfter=1 * mm,
    )
    s["project_header"] = ParagraphStyle(
        "project_header", parent=base["Normal"],
        fontName=FONT_NAME, fontSize=9, leading=13,
        spaceBefore=2 * mm, spaceAfter=1 * mm,
    )
    s["qual"] = ParagraphStyle(
        "qual", parent=base["Normal"],
        fontName=FONT_NAME, fontSize=9, leading=14,
    )
    return s


def _escape(text: str) -> str:
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _nl2br(text: str) -> str:
    return _escape(text).replace("\n", "<br/>")


def _format_period(start_date: str, end_date: str | None, is_current: bool) -> str:
    start = start_date.replace("-", " 年 ") + " 月" if "-" in start_date else start_date
    if is_current:
        return f"{start}～現在"
    end = end_date.replace("-", " 年 ") + " 月" if end_date and "-" in end_date else (end_date or "")
    return f"{start}～{end}"


def _build_project_table(project: dict, styles: dict) -> list:
    """Build table rows for a single project."""
    elements = []
    s = styles

    proj_name = _escape(project.get("name", ""))
    role = _escape(project.get("role", ""))
    header_parts = []
    if proj_name:
        header_parts.append(proj_name)
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
        left_parts.append(f"<b>【業務内容】</b><br/>{_nl2br(project['description'])}")
    if project.get("achievements"):
        left_parts.append(f"<b>【実績・取り組み】</b><br/>{_nl2br(project['achievements'])}")
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
        right_parts.append(f"<b>【{_escape(cat)}】</b><br/>{_escape(', '.join(names))}")
    right_content = "<br/>".join(right_parts) if right_parts else "-"

    scale_raw = project.get("scale", "")
    scale = f"{_escape(scale_raw)}名" if scale_raw else "-"

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
    _register_font()
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

    s = _styles()
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
    elements.append(Paragraph(f"{_escape(record_date)}現在", s["date"]))
    full_name = resume.get("full_name") or ""
    elements.append(Paragraph(f"氏名　{_escape(full_name)}", s["name"]))

    # 職務要約
    elements.append(Paragraph("■職務要約", s["section_header"]))
    elements.append(Paragraph(_nl2br(resume.get("career_summary", "")), s["body"]))

    # 職務経歴
    elements.append(Paragraph("■職務経歴", s["section_header"]))
    experiences = resume.get("experiences", [])
    if not experiences:
        elements.append(Paragraph("-", s["body"]))
    else:
        for exp in experiences:
            period = _format_period(
                exp["start_date"], exp.get("end_date"), exp.get("is_current", False)
            )
            company = _escape(exp["company"])

            # Company info
            biz = _escape(exp.get("business_description") or exp.get("title", ""))
            capital_raw = exp.get("capital", "")
            emp_raw = exp.get("employee_count", "")
            capital = f"{_escape(capital_raw)}千万円" if capital_raw else ""
            emp = f"{_escape(emp_raw)}名" if emp_raw else ""
            info_parts = [f"事業内容：{biz}"]
            if capital:
                info_parts.append(f"資本金：{capital}")
            if emp:
                info_parts.append(f"従業員数：{emp}")

            # Build inner content for this company
            inner = []

            # Projects
            projects = exp.get("projects", [])
            if projects:
                for proj in projects:
                    proj_elements = _build_project_table(proj, s)
                    inner.extend(proj_elements)
                    inner.append(Spacer(1, 2 * mm))
            else:
                compat_project = {
                    "name": "",
                    "role": "",
                    "description": exp.get("description", ""),
                    "achievements": exp.get("achievements", ""),
                    "scale": exp.get("employee_count", ""),
                    "technology_stacks": exp.get("technology_stacks", []),
                }
                proj_elements = _build_project_table(compat_project, s)
                inner.extend(proj_elements)

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
            name = _escape(q.get("name", ""))
            raw_date = q.get("acquired_date", "")
            if raw_date and "-" in raw_date:
                dp = raw_date.split("-")
                if len(dp) == 3:
                    date_str = f"{dp[0]}年{dp[1].lstrip('0')}月{dp[2].lstrip('0')}日取得"
                elif len(dp) == 2:
                    date_str = f"{dp[0]}年{dp[1].lstrip('0')}月取得"
                else:
                    date_str = f"{_escape(raw_date)}取得"
            else:
                date_str = f"{_escape(raw_date)}取得" if raw_date else ""
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
    elements.append(Paragraph(_nl2br(resume.get("self_pr", "")), s["body"]))

    doc.build(elements, onFirstPage=_add_page_number, onLaterPages=_add_page_number)
    buffer.seek(0)
    return buffer.getvalue()


def build_rirekisho_pdf(rirekisho: dict) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN, bottomMargin=MARGIN,
    )

    s = _styles()
    elements = []

    elements.append(Paragraph("履 歴 書", s["title"]))

    record_date = rirekisho.get("record_date") or ""
    if record_date and "-" in record_date:
        parts = record_date.split("-")
        if len(parts) >= 2:
            record_date = f"{parts[0]} 年 {parts[1].lstrip('0')} 月"
        if len(parts) == 3:
            record_date += f" {parts[2].lstrip('0')} 日"
    elements.append(Paragraph(f"{_escape(record_date)}現在", s["date"]))
    full_name = rirekisho.get("full_name") or ""
    elements.append(Paragraph(f"氏名　{_escape(full_name)}", s["name"]))

    elements.append(Paragraph("■連絡先", s["section_header"]))
    contact_data = [
        ["郵便番号", rirekisho.get("postal_code", "")],
        ["都道府県", rirekisho.get("prefecture", "")],
        ["住所", rirekisho.get("address", "")],
        ["メールアドレス", rirekisho.get("email", "")],
        ["電話番号", rirekisho.get("phone", "")],
    ]
    contact_table_data = [
        [
            Paragraph(f"<b>{_escape(label)}</b>", s["body_small"]),
            Paragraph(_escape(value), s["body_small"]),
        ]
        for label, value in contact_data
    ]
    ct = Table(contact_table_data, colWidths=[35 * mm, 140 * mm])
    ct.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
    ]))
    elements.append(ct)

    elements.append(Paragraph("■志望動機", s["section_header"]))
    elements.append(Paragraph(_nl2br(rirekisho.get("motivation", "")), s["body"]))

    elements.append(Paragraph("■学歴", s["section_header"]))
    educations = rirekisho.get("educations", [])
    if not educations:
        elements.append(Paragraph("-", s["body"]))
    else:
        for edu in educations:
            elements.append(Paragraph(
                f"{_escape(edu.get('date', ''))}　{_escape(edu.get('name', ''))}",
                s["body"],
            ))

    elements.append(Paragraph("■職歴", s["section_header"]))
    work_histories = rirekisho.get("work_histories", [])
    if not work_histories:
        elements.append(Paragraph("-", s["body"]))
    else:
        for wh in work_histories:
            elements.append(Paragraph(
                f"{_escape(wh.get('date', ''))}　{_escape(wh.get('name', ''))}",
                s["body"],
            ))

    doc.build(elements, onFirstPage=_add_page_number, onLaterPages=_add_page_number)
    buffer.seek(0)
    return buffer.getvalue()
