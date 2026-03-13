import base64
import logging
import re
from io import BytesIO
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Frame, Paragraph

_FONT_DIR = Path(__file__).resolve().parent.parent.parent.parent / "fonts"
_FONT_REGISTERED = False
FONT_NAME = "NotoSansJP"


def register_font() -> None:
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


def styles() -> dict:
    register_font()
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


def escape(text: str) -> str:
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def nl2br(text: str) -> str:
    return escape(text).replace("\n", "<br/>")


def format_period(start_date: str, end_date: str | None, is_current: bool) -> str:
    start = start_date.replace("-", " 年 ") + " 月" if "-" in start_date else start_date
    if is_current:
        return f"{start}～現在"
    end = end_date.replace("-", " 年 ") + " 月" if end_date and "-" in end_date else (end_date or "")
    return f"{start}～{end}"


def parse_date_ym(date_str: str) -> tuple[str, str]:
    """Parse 'YYYY-MM' or 'YYYY-MM-DD' into (year, month)."""
    if not date_str or "-" not in date_str:
        return ("", "")
    parts = date_str.split("-")
    year = parts[0]
    month = parts[1].lstrip("0") if len(parts) >= 2 else ""
    return (year, month)


def decode_photo(data_url: str | None) -> BytesIO | None:
    """Decode base64 data URL to BytesIO. Returns None on error."""
    if not data_url:
        return None
    try:
        match = re.match(r"data:[^;]+;base64,(.+)", data_url, re.DOTALL)
        if not match:
            return None
        raw = base64.b64decode(match.group(1))
        return BytesIO(raw)
    except Exception:
        logging.warning("Failed to decode photo data URL", exc_info=True)
        return None


def format_record_date(record_date: str) -> str:
    """Format record_date string for display."""
    if record_date and "-" in record_date:
        parts = record_date.split("-")
        if len(parts) >= 2:
            formatted = f"{parts[0]}年{parts[1].lstrip('0')}月"
        if len(parts) == 3:
            formatted += f"{parts[2].lstrip('0')}日"
        return f"{formatted}現在"
    return f"{record_date}現在" if record_date else ""


def draw_bordered_rect(c, x: float, y: float, w: float, h: float,
                       line_width: float = 0.5) -> None:
    """Draw a bordered rectangle (y is top-edge, draws downward)."""
    c.setLineWidth(line_width)
    c.setStrokeColor(colors.black)
    c.rect(x, y - h, w, h)


def draw_cell_text(c, text: str, x: float, y: float, w: float, h: float,
                   font_size: float = 9, align: str = "left", v_center: bool = True) -> None:
    """Draw text inside a cell area. y is top-edge of cell."""
    c.setFont(FONT_NAME, font_size)
    c.setFillColor(colors.black)
    text_y = y - h / 2 - font_size * 0.3 if v_center else y - font_size - 1 * mm
    pad = 2 * mm
    if align == "left":
        c.drawString(x + pad, text_y, text)
    elif align == "center":
        c.drawCentredString(x + w / 2, text_y, text)
    elif align == "right":
        c.drawRightString(x + w - pad, text_y, text)


def draw_text_area(c, text: str, x: float, y: float, w: float, h: float,
                   font_size: float = 9, leading: float = 14) -> None:
    """Draw multi-line text in a bounded area using Frame+Paragraph."""
    register_font()
    style = ParagraphStyle(
        "text_area", fontName=FONT_NAME, fontSize=font_size,
        leading=leading, alignment=TA_LEFT,
    )
    story = [Paragraph(nl2br(text), style)]
    frame = Frame(x + 2 * mm, y - h, w - 4 * mm, h - 2 * mm,
                  leftPadding=0, rightPadding=0, topPadding=2 * mm, bottomPadding=0)
    frame.addFromList(story, c)
