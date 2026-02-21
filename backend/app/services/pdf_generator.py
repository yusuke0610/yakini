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
    pdf: canvas.Canvas, text: str, x: float, y: float, page_height: float, font_name: str, size: int = 11
) -> float:
    if y < 20 * mm:
        pdf.showPage()
        y = page_height - 20 * mm
    pdf.setFont(font_name, size)
    pdf.drawString(x, y, text)
    return y - 6 * mm


def build_resume_pdf(resume: dict) -> bytes:
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    _, height = A4

    font_name = _safe_jp_font()
    x = 18 * mm
    y = height - 20 * mm

    y = _write_line(pdf, "職務経歴書", x, y, height, font_name, 18)
    y -= 2 * mm

    y = _write_line(pdf, f"氏名: {resume['full_name']}", x, y, height, font_name)
    y = _write_line(pdf, f"メール: {resume['email']}", x, y, height, font_name)
    y = _write_line(pdf, f"電話: {resume['phone']}", x, y, height, font_name)
    y -= 2 * mm

    y = _write_line(pdf, "概要", x, y, height, font_name, 13)
    for line in str(resume["summary"]).splitlines() or [resume["summary"]]:
        y = _write_line(pdf, line, x + 4 * mm, y, height, font_name)

    y -= 2 * mm
    y = _write_line(pdf, "職務経歴", x, y, height, font_name, 13)
    for index, exp in enumerate(resume.get("experiences", []), start=1):
        y = _write_line(
            pdf,
            f"{index}. {exp['company']} / {exp['title']} ({exp['start_date']} - {exp['end_date']})",
            x + 4 * mm,
            y,
            height,
            font_name,
        )
        for line in str(exp["description"]).splitlines() or [exp["description"]]:
            y = _write_line(pdf, f"   - {line}", x + 7 * mm, y, height, font_name)

    y -= 2 * mm
    y = _write_line(pdf, "学歴", x, y, height, font_name, 13)
    for edu in resume.get("educations", []):
        y = _write_line(
            pdf,
            f"- {edu['school']} / {edu['degree']} ({edu['start_date']} - {edu['end_date']})",
            x + 4 * mm,
            y,
            height,
            font_name,
        )

    y -= 2 * mm
    y = _write_line(pdf, "スキル", x, y, height, font_name, 13)
    skills = ", ".join(resume.get("skills", [])) or "-"
    _write_line(pdf, skills, x + 4 * mm, y, height, font_name)

    pdf.save()
    buffer.seek(0)
    return buffer.getvalue()
