import logging
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from ..utils.pdf_utils import (
    FONT_NAME,
    PAGE_H,
    PAGE_W,
    decode_photo,
    draw_bordered_rect,
    draw_cell_text,
    draw_text_area,
    format_record_date,
    parse_date_ym,
    register_font,
)

# --- Rirekisho layout constants (mm) ---
_LX = 15 * mm           # left margin
_TABLE_W = 180 * mm     # full table width
_RX = _LX + _TABLE_W    # right edge
_PHOTO_W = 30 * mm
_PHOTO_H = 40 * mm
_LEFT_W = _TABLE_W - _PHOTO_W  # width left of photo area
_ROW_H = 7 * mm         # standard table row height
_LABEL_W = 25 * mm      # label column in header area

# Column widths for year|month|content table
_COL_YEAR = 20 * mm
_COL_MONTH = 12 * mm
_COL_CONTENT = _TABLE_W - _COL_YEAR - _COL_MONTH

_MAX_HISTORY_ROWS_PAGE1 = 23


def _draw_rirekisho_page1(c: canvas.Canvas, data: dict) -> list[tuple[str, str, str]]:
    """Draw page 1 of rirekisho. Returns overflow rows that didn't fit."""
    register_font()
    y = PAGE_H - 15 * mm  # current y position (top of drawing area)

    # --- Title + Date row ---
    c.setFont(FONT_NAME, 18)
    c.drawString(_LX, y - 5 * mm, "履 歴 書")
    record_date = format_record_date(data.get("record_date", ""))
    c.setFont(FONT_NAME, 9)
    c.drawRightString(_RX - _PHOTO_W, y - 5 * mm, record_date)
    y -= 13 * mm

    # --- Photo box ---
    photo_x = _RX - _PHOTO_W
    photo_y_top = y
    draw_bordered_rect(c, photo_x, photo_y_top, _PHOTO_W, _PHOTO_H)
    photo_io = decode_photo(data.get("photo"))
    if photo_io:
        try:
            c.drawImage(ImageReader(photo_io), photo_x, photo_y_top - _PHOTO_H,
                        _PHOTO_W, _PHOTO_H, preserveAspectRatio=True, anchor="c")
        except Exception:
            logging.warning("Failed to render photo on rirekisho PDF", exc_info=True)
    else:
        c.setFont(FONT_NAME, 7)
        c.setFillColor(colors.HexColor("#999999"))
        c.drawCentredString(photo_x + _PHOTO_W / 2, photo_y_top - _PHOTO_H / 2 - 2 * mm, "写真")
        c.setFillColor(colors.black)

    # --- Furigana row ---
    furigana_h = 8 * mm
    draw_bordered_rect(c, _LX, y, _LABEL_W, furigana_h)
    draw_cell_text(c, "ふりがな", _LX, y, _LABEL_W, furigana_h, font_size=7)
    draw_bordered_rect(c, _LX + _LABEL_W, y, _LEFT_W - _LABEL_W, furigana_h)
    name_furigana = data.get("name_furigana", "")
    if name_furigana:
        draw_cell_text(c, name_furigana, _LX + _LABEL_W, y, _LEFT_W - _LABEL_W, furigana_h, font_size=8)
    y -= furigana_h

    # --- Name row ---
    name_h = 16 * mm
    draw_bordered_rect(c, _LX, y, _LABEL_W, name_h)
    draw_cell_text(c, "氏　名", _LX, y, _LABEL_W, name_h, font_size=9)
    draw_bordered_rect(c, _LX + _LABEL_W, y, _LEFT_W - _LABEL_W, name_h)
    full_name = data.get("full_name", "")
    draw_cell_text(c, full_name, _LX + _LABEL_W, y, _LEFT_W - _LABEL_W, name_h, font_size=14)
    y -= name_h

    # --- Birthday / Gender row ---
    bd_h = 10 * mm
    draw_bordered_rect(c, _LX, y, _LEFT_W, bd_h)
    draw_cell_text(c, "生年月日", _LX, y, _LABEL_W, bd_h, font_size=8)
    # Draw gender separator
    gender_w = 25 * mm
    c.setLineWidth(0.5)
    c.line(_LX + _LEFT_W - gender_w, y, _LX + _LEFT_W - gender_w, y - bd_h)
    gender_raw = data.get("gender", "")
    gender_labels = {"male": "男", "female": "女"}
    gender_text = gender_labels.get(gender_raw, "")
    if gender_text:
        draw_cell_text(c, gender_text, _LX + _LEFT_W - gender_w, y, gender_w, bd_h, font_size=9, align="center")
    else:
        draw_cell_text(c, "性別", _LX + _LEFT_W - gender_w, y, gender_w, bd_h, font_size=8, align="center")
    # Photo area extends below — draw bottom border of photo
    if y > photo_y_top - _PHOTO_H:
        pass  # photo still extends below
    y -= bd_h

    # --- Address furigana row ---
    addr_furigana_h = 8 * mm
    draw_bordered_rect(c, _LX, y, _LABEL_W, addr_furigana_h)
    draw_cell_text(c, "ふりがな", _LX, y, _LABEL_W, addr_furigana_h, font_size=7)
    draw_bordered_rect(c, _LX + _LABEL_W, y, _TABLE_W - _LABEL_W, addr_furigana_h)
    address_furigana = data.get("address_furigana", "")
    if address_furigana:
        draw_cell_text(c, address_furigana, _LX + _LABEL_W, y, _TABLE_W - _LABEL_W, addr_furigana_h, font_size=8)
    y -= addr_furigana_h

    # --- Address row ---
    addr_row_h = 20 * mm
    draw_bordered_rect(c, _LX, y, _LABEL_W, addr_row_h)
    draw_cell_text(c, "現住所", _LX, y, _LABEL_W, addr_row_h, font_size=8)
    draw_bordered_rect(c, _LX + _LABEL_W, y, _TABLE_W - _LABEL_W, addr_row_h)
    prefecture = data.get("prefecture", "")
    address = data.get("address", "")
    full_address = f"{prefecture}{address}"
    draw_cell_text(c, full_address, _LX + _LABEL_W, y, _TABLE_W - _LABEL_W, addr_row_h, font_size=9, v_center=False)
    y -= addr_row_h

    # --- Contact block (連絡先: 電話 / メール) ---
    contact_label_h = 8 * mm
    contact_body_h = 14 * mm
    draw_bordered_rect(c, _LX, y, _LABEL_W, contact_label_h + contact_body_h)
    draw_cell_text(c, "連絡先", _LX, y, _LABEL_W, contact_label_h + contact_body_h, font_size=8)
    draw_bordered_rect(c, _LX + _LABEL_W, y, _TABLE_W - _LABEL_W, contact_label_h + contact_body_h)
    phone = data.get("phone", "")
    email = data.get("email", "")
    contact_x = _LX + _LABEL_W + 2 * mm
    c.setFont(FONT_NAME, 9)
    c.drawString(contact_x, y - 5 * mm, f"電話: {phone}")
    c.drawString(contact_x, y - 12 * mm, f"E-mail: {email}")
    y -= (contact_label_h + contact_body_h)

    # --- Education + Work History table ---
    y -= 4 * mm  # spacing

    # Build combined rows: [(year, month, content), ...]
    all_rows: list[tuple[str, str, str]] = []

    # Education section
    educations = data.get("educations", [])
    all_rows.append(("", "", "学　歴"))
    for edu in educations:
        date_str = edu.get("date", "")
        yr, mo = parse_date_ym(date_str)
        all_rows.append((yr, mo, edu.get("name", "")))

    # Work history section
    work_histories = data.get("work_histories", [])
    all_rows.append(("", "", "職　歴"))
    for wh in work_histories:
        date_str = wh.get("date", "")
        yr, mo = parse_date_ym(date_str)
        all_rows.append((yr, mo, wh.get("name", "")))

    # Draw table header
    header_h = _ROW_H
    draw_bordered_rect(c, _LX, y, _COL_YEAR, header_h)
    draw_cell_text(c, "年", _LX, y, _COL_YEAR, header_h, font_size=8, align="center")
    draw_bordered_rect(c, _LX + _COL_YEAR, y, _COL_MONTH, header_h)
    draw_cell_text(c, "月", _LX + _COL_YEAR, y, _COL_MONTH, header_h, font_size=8, align="center")
    draw_bordered_rect(c, _LX + _COL_YEAR + _COL_MONTH, y, _COL_CONTENT, header_h)
    draw_cell_text(c, "学歴・職歴", _LX + _COL_YEAR + _COL_MONTH, y, _COL_CONTENT, header_h, font_size=8, align="center")
    y -= header_h

    # Draw rows
    rows_drawn = 0
    overflow: list[tuple[str, str, str]] = []
    for i, (yr, mo, content) in enumerate(all_rows):
        if rows_drawn >= _MAX_HISTORY_ROWS_PAGE1:
            overflow = all_rows[i:]
            break
        draw_bordered_rect(c, _LX, y, _COL_YEAR, _ROW_H)
        draw_cell_text(c, yr, _LX, y, _COL_YEAR, _ROW_H, font_size=8, align="center")
        draw_bordered_rect(c, _LX + _COL_YEAR, y, _COL_MONTH, _ROW_H)
        draw_cell_text(c, mo, _LX + _COL_YEAR, y, _COL_MONTH, _ROW_H, font_size=8, align="center")
        draw_bordered_rect(c, _LX + _COL_YEAR + _COL_MONTH, y, _COL_CONTENT, _ROW_H)
        # Center the label rows
        is_label = content in ("学　歴", "職　歴")
        draw_cell_text(c, content, _LX + _COL_YEAR + _COL_MONTH, y, _COL_CONTENT, _ROW_H,
                       font_size=8, align="center" if is_label else "left")
        y -= _ROW_H
        rows_drawn += 1

    # Fill remaining empty rows
    while rows_drawn < _MAX_HISTORY_ROWS_PAGE1:
        draw_bordered_rect(c, _LX, y, _COL_YEAR, _ROW_H)
        draw_bordered_rect(c, _LX + _COL_YEAR, y, _COL_MONTH, _ROW_H)
        draw_bordered_rect(c, _LX + _COL_YEAR + _COL_MONTH, y, _COL_CONTENT, _ROW_H)
        y -= _ROW_H
        rows_drawn += 1

    return overflow


def _draw_rirekisho_page2(c: canvas.Canvas, data: dict,
                          overflow_rows: list[tuple[str, str, str]]) -> None:
    """Draw page 2 of rirekisho."""
    register_font()
    y = PAGE_H - 15 * mm

    # --- Overflow history rows ---
    if overflow_rows:
        header_h = _ROW_H
        draw_bordered_rect(c, _LX, y, _COL_YEAR, header_h)
        draw_cell_text(c, "年", _LX, y, _COL_YEAR, header_h, font_size=8, align="center")
        draw_bordered_rect(c, _LX + _COL_YEAR, y, _COL_MONTH, header_h)
        draw_cell_text(c, "月", _LX + _COL_YEAR, y, _COL_MONTH, header_h, font_size=8, align="center")
        draw_bordered_rect(c, _LX + _COL_YEAR + _COL_MONTH, y, _COL_CONTENT, header_h)
        draw_cell_text(
            c, "学歴・職歴（続き）", _LX + _COL_YEAR + _COL_MONTH, y,
            _COL_CONTENT, header_h, font_size=8, align="center",
        )
        y -= header_h

        for yr, mo, content in overflow_rows:
            draw_bordered_rect(c, _LX, y, _COL_YEAR, _ROW_H)
            draw_cell_text(c, yr, _LX, y, _COL_YEAR, _ROW_H, font_size=8, align="center")
            draw_bordered_rect(c, _LX + _COL_YEAR, y, _COL_MONTH, _ROW_H)
            draw_cell_text(c, mo, _LX + _COL_YEAR, y, _COL_MONTH, _ROW_H, font_size=8, align="center")
            draw_bordered_rect(c, _LX + _COL_YEAR + _COL_MONTH, y, _COL_CONTENT, _ROW_H)
            is_label = content in ("学　歴", "職　歴")
            draw_cell_text(c, content, _LX + _COL_YEAR + _COL_MONTH, y, _COL_CONTENT, _ROW_H,
                           font_size=8, align="center" if is_label else "left")
            y -= _ROW_H
        y -= 4 * mm

    # --- Qualifications table ---
    qualifications = data.get("qualifications", [])
    qual_header_h = _ROW_H
    draw_bordered_rect(c, _LX, y, _COL_YEAR, qual_header_h)
    draw_cell_text(c, "年", _LX, y, _COL_YEAR, qual_header_h, font_size=8, align="center")
    draw_bordered_rect(c, _LX + _COL_YEAR, y, _COL_MONTH, qual_header_h)
    draw_cell_text(c, "月", _LX + _COL_YEAR, y, _COL_MONTH, qual_header_h, font_size=8, align="center")
    draw_bordered_rect(c, _LX + _COL_YEAR + _COL_MONTH, y, _COL_CONTENT, qual_header_h)
    draw_cell_text(
        c, "免許・資格", _LX + _COL_YEAR + _COL_MONTH, y,
        _COL_CONTENT, qual_header_h, font_size=8, align="center",
    )
    y -= qual_header_h

    qual_max_rows = 10
    qual_rows_drawn = 0
    for q in qualifications:
        if qual_rows_drawn >= qual_max_rows:
            break
        raw_date = q.get("acquired_date", "")
        yr, mo = parse_date_ym(raw_date)
        name = q.get("name", "")
        draw_bordered_rect(c, _LX, y, _COL_YEAR, _ROW_H)
        draw_cell_text(c, yr, _LX, y, _COL_YEAR, _ROW_H, font_size=8, align="center")
        draw_bordered_rect(c, _LX + _COL_YEAR, y, _COL_MONTH, _ROW_H)
        draw_cell_text(c, mo, _LX + _COL_YEAR, y, _COL_MONTH, _ROW_H, font_size=8, align="center")
        draw_bordered_rect(c, _LX + _COL_YEAR + _COL_MONTH, y, _COL_CONTENT, _ROW_H)
        draw_cell_text(c, name, _LX + _COL_YEAR + _COL_MONTH, y, _COL_CONTENT, _ROW_H, font_size=8)
        y -= _ROW_H
        qual_rows_drawn += 1

    # Fill remaining empty rows
    while qual_rows_drawn < qual_max_rows:
        draw_bordered_rect(c, _LX, y, _COL_YEAR, _ROW_H)
        draw_bordered_rect(c, _LX + _COL_YEAR, y, _COL_MONTH, _ROW_H)
        draw_bordered_rect(c, _LX + _COL_YEAR + _COL_MONTH, y, _COL_CONTENT, _ROW_H)
        y -= _ROW_H
        qual_rows_drawn += 1

    y -= 4 * mm

    # --- Motivation / Self-PR area ---
    motivation_label_h = _ROW_H
    motivation_area_h = 55 * mm
    draw_bordered_rect(c, _LX, y, _TABLE_W, motivation_label_h)
    draw_cell_text(c, "志望の動機、自己PRなど", _LX, y, _TABLE_W, motivation_label_h, font_size=8)
    y -= motivation_label_h
    draw_bordered_rect(c, _LX, y, _TABLE_W, motivation_area_h)
    motivation = data.get("motivation", "")
    if motivation:
        draw_text_area(c, motivation, _LX, y, _TABLE_W, motivation_area_h, font_size=9, leading=14)
    y -= motivation_area_h

    y -= 4 * mm

    # --- Personal preferences area ---
    pref_label_h = _ROW_H
    pref_area_h = 45 * mm
    draw_bordered_rect(c, _LX, y, _TABLE_W, pref_label_h)
    draw_cell_text(c, "本人希望記入欄（特に給料・職種・勤務時間・勤務地・その他についての希望などがあれば記入）",
                   _LX, y, _TABLE_W, pref_label_h, font_size=6)
    y -= pref_label_h
    draw_bordered_rect(c, _LX, y, _TABLE_W, pref_area_h)
    personal_preferences = data.get("personal_preferences", "")
    if personal_preferences:
        draw_text_area(c, personal_preferences, _LX, y, _TABLE_W, pref_area_h, font_size=9, leading=14)
    y -= pref_area_h


def _draw_page_num(c: canvas.Canvas, page: int, total: int) -> None:
    """Draw page number at bottom center."""
    c.setFont(FONT_NAME, 8)
    c.drawCentredString(PAGE_W / 2, 10 * mm, f"{page} / {total}")


def build_rirekisho_pdf(rirekisho: dict) -> bytes:
    register_font()
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    overflow = _draw_rirekisho_page1(c, rirekisho)
    _draw_page_num(c, 1, 2)
    c.showPage()

    _draw_rirekisho_page2(c, rirekisho, overflow)
    _draw_page_num(c, 2, 2)
    c.showPage()

    c.save()
    buffer.seek(0)
    return buffer.getvalue()
