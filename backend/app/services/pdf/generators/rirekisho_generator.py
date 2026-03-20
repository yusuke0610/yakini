import re
from html import escape as _html_escape
from pathlib import Path

import markdown
import weasyprint

_CSS_PATH = Path(__file__).resolve().parent.parent / "templates" / "rirekisho.css"
_FONT_PATH = (
    Path(__file__).resolve().parent.parent.parent.parent / "fonts" / "NotoSansJP-Regular.ttf"
)

_MAX_HISTORY_ROWS_PAGE1 = 23
_QUAL_MAX_ROWS = 10


def _esc(text: str) -> str:
    """HTMLエスケープのショートカット"""
    return _html_escape(str(text))


def _md(text: str) -> str:
    """Markdownテキストを安全にHTMLに変換する"""
    return markdown.markdown(str(text), extensions=["tables"])


def _parse_date_ym(date_str: str) -> tuple[str, str]:
    """'YYYY-MM' または 'YYYY-MM-DD' を (年, 月) にパースする"""
    if not date_str or "-" not in date_str:
        return ("", "")
    parts = date_str.split("-")
    year = parts[0]
    month = parts[1].lstrip("0") if len(parts) >= 2 else ""
    return (year, month)


def _format_record_date(record_date: str) -> str:
    """記載日を表示用にフォーマットする"""
    if record_date and "-" in record_date:
        parts = record_date.split("-")
        result = ""
        if len(parts) >= 2:
            result = f"{parts[0]}年{parts[1].lstrip('0')}月"
        if len(parts) == 3:
            result += f"{parts[2].lstrip('0')}日"
        return f"{result}現在"
    return f"{record_date}現在" if record_date else ""


def _build_photo_html(data: dict) -> str:
    """写真セルの中身を組み立てる"""
    photo_data = data.get("photo")
    if not photo_data:
        return "写真"
    # data:image/xxx;base64,... 形式をそのままimgタグに埋め込む
    match = re.match(r"data:[^;]+;base64,.+", str(photo_data), re.DOTALL)
    if match:
        return f'<img src="{_esc(photo_data)}" alt="写真" />'
    return "写真"


def _build_history_rows(data: dict) -> list[tuple[str, str, str]]:
    """学歴・職歴の行データを組み立てる"""
    rows: list[tuple[str, str, str]] = []

    # 学歴セクション
    educations = data.get("educations", [])
    rows.append(("", "", "学　歴"))
    for edu in educations:
        yr, mo = _parse_date_ym(edu.get("date", ""))
        rows.append((yr, mo, edu.get("name", "")))

    # 職歴セクション
    work_histories = data.get("work_histories", [])
    rows.append(("", "", "職　歴"))
    for wh in work_histories:
        yr, mo = _parse_date_ym(wh.get("date", ""))
        rows.append((yr, mo, wh.get("name", "")))

    return rows


def _build_history_table_html(
    rows: list[tuple[str, str, str]],
    header_label: str = "学歴・職歴",
    max_rows: int | None = None,
) -> tuple[str, list[tuple[str, str, str]]]:
    """学歴・職歴テーブルのHTMLを組み立てる。はみ出し行があれば返す。"""
    parts: list[str] = []
    parts.append('<table class="history-table">')
    parts.append(
        "<tr>"
        f'<th class="year">年</th>'
        f'<th class="month">月</th>'
        f"<th>{_esc(header_label)}</th>"
        "</tr>"
    )

    overflow: list[tuple[str, str, str]] = []
    drawn = 0
    for i, (yr, mo, content) in enumerate(rows):
        if max_rows is not None and drawn >= max_rows:
            overflow = rows[i:]
            break
        is_label = content in ("学　歴", "職　歴")
        td_class = ' class="section-label"' if is_label else ' class="content"'
        parts.append(
            f"<tr>"
            f'<td class="year">{_esc(yr)}</td>'
            f'<td class="month">{_esc(mo)}</td>'
            f"<td{td_class}>{_esc(content)}</td>"
            f"</tr>"
        )
        drawn += 1

    # 空行で埋める
    if max_rows is not None:
        while drawn < max_rows:
            parts.append(
                '<tr><td class="year"></td>'
                '<td class="month"></td>'
                '<td class="content"></td></tr>'
            )
            drawn += 1

    parts.append("</table>")
    return "\n".join(parts), overflow


def _build_qual_table_html(data: dict) -> str:
    """免許・資格テーブルのHTMLを組み立てる"""
    qualifications = data.get("qualifications", [])
    parts: list[str] = []
    parts.append('<table class="qual-table">')
    parts.append(
        "<tr>" '<th class="year">年</th>' '<th class="month">月</th>' "<th>免許・資格</th>" "</tr>"
    )

    drawn = 0
    for q in qualifications:
        if drawn >= _QUAL_MAX_ROWS:
            break
        yr, mo = _parse_date_ym(q.get("acquired_date", ""))
        name = _esc(q.get("name", ""))
        parts.append(
            f"<tr>"
            f'<td class="year">{yr}</td>'
            f'<td class="month">{mo}</td>'
            f'<td class="content">{name}</td>'
            f"</tr>"
        )
        drawn += 1

    # 空行で埋める
    while drawn < _QUAL_MAX_ROWS:
        parts.append(
            '<tr><td class="year"></td>' '<td class="month"></td>' '<td class="content"></td></tr>'
        )
        drawn += 1

    parts.append("</table>")
    return "\n".join(parts)


def _build_html(data: dict) -> str:
    """履歴書データからHTML文字列を組み立てる"""
    parts: list[str] = []

    # --- タイトル + 日付 ---
    record_date = _format_record_date(data.get("record_date", ""))
    parts.append(
        '<div class="title-row">'
        "<h1>履 歴 書</h1>"
        f'<span class="date">{_esc(record_date)}</span>'
        "</div>"
    )

    # --- 個人情報テーブル ---
    name_furigana = data.get("name_furigana", "")
    full_name = data.get("full_name", "")
    gender_raw = data.get("gender", "")
    gender_labels = {"male": "男", "female": "女"}
    gender_text = gender_labels.get(gender_raw, "")
    birthday = data.get("birthday", "")
    bd_display = ""
    if birthday and "-" in birthday:
        bd_parts = birthday.split("-")
        if len(bd_parts) >= 2:
            bd_display = f"{bd_parts[0]}年{bd_parts[1].lstrip('0')}月"
        if len(bd_parts) == 3:
            bd_display += f"{bd_parts[2].lstrip('0')}日生"
    gender_html = "※性別"
    if gender_text:
        gender_html = '<span class="gender-note">※性別</span><br/>' f"{_esc(gender_text)}"

    photo_html = _build_photo_html(data)
    address_furigana = data.get("address_furigana", "")
    postal_code = data.get("postal_code", "")
    prefecture = data.get("prefecture", "")
    address = data.get("address", "")
    postal_prefix = f"〒{postal_code} " if postal_code else ""
    full_address = f"{postal_prefix}{prefecture}{address}"
    phone = data.get("phone", "")
    email = data.get("email", "")

    parts.append('<table class="personal-info">')
    # ふりがな行 + 写真（rowspan=3）
    parts.append(
        "<tr>"
        '<td class="label" rowspan="1">ふりがな</td>'
        f'<td class="furigana" colspan="2">{_esc(name_furigana)}</td>'
        f'<td class="photo" rowspan="3">{photo_html}</td>'
        "</tr>"
    )
    # 氏名行
    parts.append(
        "<tr>"
        '<td class="label">氏　名</td>'
        f'<td class="name" colspan="2">{_esc(full_name)}</td>'
        "</tr>"
    )
    # 生年月日 / 性別行
    parts.append(
        "<tr>"
        f'<td class="label">生年月日</td>'
        f'<td class="bd">{_esc(bd_display)}</td>'
        '<td class="gender">'
        f"{gender_html}"
        "</td>"
        "</tr>"
    )
    # 住所ふりがな行
    parts.append(
        "<tr>"
        '<td class="label">ふりがな</td>'
        f'<td class="address-furigana" colspan="3">{_esc(address_furigana)}</td>'
        "</tr>"
    )
    # 住所行
    parts.append(
        "<tr>"
        '<td class="label">現住所</td>'
        f'<td class="address" colspan="3">{_esc(full_address)}</td>'
        "</tr>"
    )
    # 連絡先行
    contact_lines = []
    if phone:
        contact_lines.append(f"電話: {_esc(phone)}")
    if email:
        contact_lines.append(f"E-mail: {_esc(email)}")
    contact_html = "<br/>".join(contact_lines)
    parts.append(
        "<tr>"
        '<td class="label">連絡先</td>'
        f'<td class="contact" colspan="3">{contact_html}</td>'
        "</tr>"
    )
    parts.append("</table>")

    # --- 学歴・職歴テーブル (1ページ目) ---
    all_rows = _build_history_rows(data)
    history_html, overflow = _build_history_table_html(
        all_rows,
        header_label="学歴・職歴",
        max_rows=_MAX_HISTORY_ROWS_PAGE1,
    )
    parts.append(history_html)

    # --- 2ページ目 ---
    parts.append('<div class="page-break"></div>')

    # はみ出した学歴・職歴
    if overflow:
        overflow_html, _ = _build_history_table_html(
            overflow,
            header_label="学歴・職歴（続き）",
        )
        parts.append(overflow_html)

    # --- 免許・資格テーブル ---
    parts.append(_build_qual_table_html(data))

    # --- 志望動機 ---
    motivation = data.get("motivation", "")
    parts.append('<div class="text-block">')
    parts.append('<div class="text-block-header">志望の動機、自己PRなど</div>')
    parts.append(
        f'<div class="text-block-body motivation">{_md(motivation) if motivation else ""}</div>'
    )
    parts.append("</div>")

    # --- 本人希望記入欄 ---
    personal_preferences = data.get("personal_preferences", "")
    parts.append('<div class="text-block">')
    parts.append(
        '<div class="text-block-header">' "本人希望記入欄（特に給料・職種・勤務時間・勤務地・その他についての希望などがあれば記入）" "</div>"
    )
    parts.append(
        f'<div class="text-block-body">'
        f'{_md(personal_preferences) if personal_preferences else ""}</div>'
    )
    parts.append("</div>")

    return "\n".join(parts)


def build_rirekisho_pdf(rirekisho: dict) -> bytes:
    """履歴書データからPDFバイト列を生成する"""
    html_body = _build_html(rirekisho)

    # CSSテンプレートを読み込み、フォントパスを埋め込む
    css_text = _CSS_PATH.read_text(encoding="utf-8")
    css_text = css_text.replace(
        "{{ font_path }}",
        _FONT_PATH.as_uri(),
    )

    full_html = (
        "<!DOCTYPE html>"
        '<html lang="ja"><head>'
        '<meta charset="utf-8">'
        f"<style>{css_text}</style>"
        f"</head><body>{html_body}</body></html>"
    )

    pdf_bytes = weasyprint.HTML(string=full_html).write_pdf()
    return pdf_bytes
