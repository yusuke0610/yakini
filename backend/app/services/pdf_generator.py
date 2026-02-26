from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfgen import canvas


def _safe_jp_font() -> str:
    try:
        pdfmetrics.registerFont(UnicodeCIDFont("HeiseiKakuGo-W5"))
        return "HeiseiKakuGo-W5"
    except Exception:
        return "Helvetica"


def _write_line(
    pdf: canvas.Canvas,
    text: str,
    x: float,
    y: float,
    page_height: float,
    font_name: str,
    size: int = 11,
) -> float:
    if y < 20 * mm:
        pdf.showPage()
        y = page_height - 20 * mm
    pdf.setFont(font_name, size)
    pdf.drawString(x, y, text)
    return y - 6 * mm


def _write_multiline(
    pdf: canvas.Canvas,
    text: str,
    x: float,
    y: float,
    page_height: float,
    font_name: str,
    size: int = 11,
) -> float:
    for line in str(text).splitlines() or [str(text)]:
        y = _write_line(pdf, line, x, y, page_height, font_name, size)
    return y


def _experience_period(start_date: str, end_date: str | None, is_current: bool) -> str:
    if is_current:
        return f"{start_date} - 在職"
    return f"{start_date} - {end_date}"


def _write_basic_header(document_name: str, payload: dict, pdf: canvas.Canvas, page_height: float, font_name: str) -> float:
    x = 18 * mm
    y = page_height - 20 * mm
    y = _write_line(pdf, document_name, x, y, page_height, font_name, 18)
    y -= 2 * mm

    full_name = payload.get("full_name") or "-"
    record_date = payload.get("record_date") or "-"

    y = _write_line(pdf, f"氏名: {full_name}", x, y, page_height, font_name)
    y = _write_line(pdf, f"記載日: {record_date}", x, y, page_height, font_name)

    y -= 2 * mm
    y = _write_line(pdf, "資格", x, y, page_height, font_name, 13)
    qualifications = payload.get("qualifications", [])
    if not qualifications:
        y = _write_line(pdf, "-", x + 4 * mm, y, page_height, font_name)
    else:
        for qual in qualifications:
            y = _write_line(
                pdf,
                f"- {qual['acquired_date']} {qual['name']}",
                x + 4 * mm,
                y,
                page_height,
                font_name,
            )

    return y


def build_resume_pdf(resume: dict) -> bytes:
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    _, height = A4

    font_name = _safe_jp_font()
    x = 18 * mm

    y = _write_basic_header("職務経歴書", resume, pdf, height, font_name)
    y -= 2 * mm

    y = _write_line(pdf, "職務要約", x, y, height, font_name, 13)
    y = _write_multiline(pdf, resume.get("career_summary", ""), x + 4 * mm, y, height, font_name)

    y -= 2 * mm
    y = _write_line(pdf, "自己PR", x, y, height, font_name, 13)
    y = _write_multiline(pdf, resume.get("self_pr", ""), x + 4 * mm, y, height, font_name)

    y -= 2 * mm
    y = _write_line(pdf, "職務経歴", x, y, height, font_name, 13)
    experiences = resume.get("experiences", [])
    if not experiences:
        y = _write_line(pdf, "-", x + 4 * mm, y, height, font_name)
    else:
        for index, exp in enumerate(experiences, start=1):
            period = _experience_period(exp["start_date"], exp.get("end_date"), exp.get("is_current", False))
            y = _write_line(
                pdf,
                f"{index}. {exp['company']} / {exp['title']} ({period})",
                x + 4 * mm,
                y,
                height,
                font_name,
            )
            y = _write_line(
                pdf,
                f"   従業員数: {exp['employee_count']} / 資本金: {exp['capital']}",
                x + 7 * mm,
                y,
                height,
                font_name,
            )
            y = _write_line(pdf, "   実績:", x + 7 * mm, y, height, font_name)
            y = _write_multiline(
                pdf,
                exp["achievements"],
                x + 10 * mm,
                y,
                height,
                font_name,
            )
            y = _write_line(pdf, "   業務内容:", x + 7 * mm, y, height, font_name)
            y = _write_multiline(
                pdf,
                exp["description"],
                x + 10 * mm,
                y,
                height,
                font_name,
            )
            technology_stacks = exp.get("technology_stacks", [])
            y = _write_line(pdf, "   技術スタック:", x + 7 * mm, y, height, font_name)
            if not technology_stacks:
                y = _write_line(pdf, "   -", x + 10 * mm, y, height, font_name)
            else:
                for stack in technology_stacks:
                    category = stack.get("category", "")
                    name = stack.get("name", "")
                    y = _write_line(
                        pdf,
                        f"   - {category}: {name}",
                        x + 10 * mm,
                        y,
                        height,
                        font_name,
                    )

    pdf.save()
    buffer.seek(0)
    return buffer.getvalue()


def build_Resume_pdf(Resume: dict) -> bytes:
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    _, height = A4

    font_name = _safe_jp_font()
    x = 18 * mm

    y = _write_basic_header("履歴書", Resume, pdf, height, font_name)
    y -= 2 * mm

    y = _write_line(pdf, f"郵便番号: {Resume['postal_code']}", x, y, height, font_name)
    y = _write_line(pdf, f"都道府県: {Resume['prefecture']}", x, y, height, font_name)
    y = _write_line(pdf, f"住所: {Resume['address']}", x, y, height, font_name)
    y = _write_line(pdf, f"メールアドレス: {Resume['email']}", x, y, height, font_name)
    y = _write_line(pdf, f"電話番号: {Resume['phone']}", x, y, height, font_name)

    y -= 2 * mm
    y = _write_line(pdf, "志望動機", x, y, height, font_name, 13)
    y = _write_multiline(pdf, Resume.get("motivation", ""), x + 4 * mm, y, height, font_name)

    y -= 2 * mm
    y = _write_line(pdf, "学歴", x, y, height, font_name, 13)
    educations = Resume.get("educations", [])
    if not educations:
        y = _write_line(pdf, "-", x + 4 * mm, y, height, font_name)
    else:
        for education in educations:
            y = _write_line(
                pdf,
                f"- {education['date']} {education['name']}",
                x + 4 * mm,
                y,
                height,
                font_name,
            )

    y -= 2 * mm
    y = _write_line(pdf, "職歴", x, y, height, font_name, 13)
    work_histories = Resume.get("work_histories", [])
    if not work_histories:
        y = _write_line(pdf, "-", x + 4 * mm, y, height, font_name)
    else:
        for work_history in work_histories:
            y = _write_line(
                pdf,
                f"- {work_history['date']} {work_history['name']}",
                x + 4 * mm,
                y,
                height,
                font_name,
            )

    pdf.save()
    buffer.seek(0)
    return buffer.getvalue()
