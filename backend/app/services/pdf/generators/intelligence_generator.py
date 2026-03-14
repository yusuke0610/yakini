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
    register_font,
    styles,
)


def _add_page_number(canvas_obj, doc):
    register_font()
    canvas_obj.saveState()
    canvas_obj.setFont(FONT_NAME, 8)
    canvas_obj.drawCentredString(PAGE_W / 2, 10 * mm, f"{canvas_obj.getPageNumber()}")
    canvas_obj.restoreState()


def build_intelligence_pdf(payload: dict) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN, bottomMargin=MARGIN,
    )

    s = styles()
    elements = []
    content_width = PAGE_W - 2 * MARGIN

    # Title
    elements.append(Paragraph("GitHub 分析レポート", s["title"]))
    elements.append(Spacer(1, 2 * mm))

    # Overview
    username = escape(payload.get("username", ""))
    repos = payload.get("repos_analyzed", 0)
    skills_count = payload.get("unique_skills", 0)
    analyzed_at = escape(payload.get("analyzed_at", ""))

    overview_data = [
        [Paragraph("<b>ユーザー</b>", s["body"]),
         Paragraph(username, s["body"])],
        [Paragraph("<b>分析リポジトリ数</b>", s["body"]),
         Paragraph(str(repos), s["body"])],
        [Paragraph("<b>ユニークスキル数</b>", s["body"]),
         Paragraph(str(skills_count), s["body"])],
        [Paragraph("<b>分析日時</b>", s["body"]),
         Paragraph(analyzed_at, s["body"])],
    ]
    overview_table = Table(overview_data, colWidths=[40 * mm, content_width - 40 * mm])
    overview_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, TABLE_BORDER),
        ("BACKGROUND", (0, 0), (0, -1), HEADER_BG),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(overview_table)
    elements.append(Spacer(1, 4 * mm))

    # AI Summary
    summary = payload.get("summary", "")
    if summary:
        elements.append(Paragraph("■ AI要約", s["section_header"]))
        elements.append(Paragraph(escape(summary).replace("\n", "<br/>"), s["body"]))
        elements.append(Spacer(1, 3 * mm))

    # Growth Trends
    growth = payload.get("growth", [])
    if growth:
        elements.append(Paragraph("■ スキル成長トレンド", s["section_header"]))

        emerging = [g for g in growth if g.get("trend") in ("emerging", "new")]
        stable = [g for g in growth if g.get("trend") == "stable"]
        declining = [g for g in growth if g.get("trend") == "declining"]

        trend_data = [
            [Paragraph("<b>カテゴリ</b>", s["body_small"]),
             Paragraph("<b>スキル</b>", s["body_small"])],
        ]
        if emerging:
            names = ", ".join(g["skill_name"] for g in emerging)
            trend_data.append([
                Paragraph("Emerging / New", s["body_small"]),
                Paragraph(escape(names), s["body_small"]),
            ])
        if stable:
            names = ", ".join(g["skill_name"] for g in stable)
            trend_data.append([
                Paragraph("Stable", s["body_small"]),
                Paragraph(escape(names), s["body_small"]),
            ])
        if declining:
            names = ", ".join(g["skill_name"] for g in declining)
            trend_data.append([
                Paragraph("Declining", s["body_small"]),
                Paragraph(escape(names), s["body_small"]),
            ])

        trend_table = Table(trend_data, colWidths=[35 * mm, content_width - 35 * mm])
        trend_table.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, TABLE_BORDER),
            ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ]))
        elements.append(trend_table)
        elements.append(Spacer(1, 3 * mm))

    # Career Prediction
    prediction = payload.get("prediction", {})
    if prediction:
        elements.append(Paragraph("■ キャリア予測", s["section_header"]))

        current = prediction.get("current_role", {})
        if current:
            role_name = escape(current.get("role_name", ""))
            conf = current.get("confidence", 0)
            matching = ", ".join(current.get("matching_skills", []))

            elements.append(Paragraph(
                f"<b>現在のロール:</b> {role_name} (確信度: {conf:.0%})",
                s["body"],
            ))
            if matching:
                elements.append(Paragraph(
                    f"<b>マッチするスキル:</b> {escape(matching)}",
                    s["body_small"],
                ))
            elements.append(Spacer(1, 2 * mm))

        next_roles = prediction.get("next_roles", [])
        if next_roles:
            elements.append(Paragraph("<b>次のキャリアステップ</b>", s["body"]))
            role_data = [[
                Paragraph("<b>ロール</b>", s["body_small"]),
                Paragraph("<b>確信度</b>", s["body_small"]),
                Paragraph("<b>不足スキル</b>", s["body_small"]),
            ]]
            for role in next_roles:
                conf = role.get("confidence", 0)
                missing = ", ".join(role.get("missing_skills", []))
                role_data.append([
                    Paragraph(escape(role.get("role_name", "")), s["body_small"]),
                    Paragraph(f"{conf:.0%}", s["body_small"]),
                    Paragraph(escape(missing) if missing else "-", s["body_small"]),
                ])
            role_table = Table(role_data, colWidths=[45 * mm, 20 * mm, content_width - 65 * mm])
            role_table.setStyle(TableStyle([
                ("GRID", (0, 0), (-1, -1), 0.5, TABLE_BORDER),
                ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ]))
            elements.append(role_table)
            elements.append(Spacer(1, 2 * mm))

        long_term = prediction.get("long_term_roles", [])
        if long_term:
            elements.append(Paragraph("<b>長期キャリア候補</b>", s["body"]))
            for role in long_term:
                conf = role.get("confidence", 0)
                elements.append(Paragraph(
                    f"・{escape(role.get('role_name', ''))} ({conf:.0%})",
                    s["body_small"],
                ))
            elements.append(Spacer(1, 2 * mm))

    # Career Simulation
    simulation = payload.get("simulation", {})
    paths = simulation.get("paths", [])
    if paths:
        elements.append(Paragraph("■ キャリアパスシミュレーション", s["section_header"]))
        for i, p in enumerate(paths, 1):
            path_str = " → ".join(p.get("path", []))
            conf = p.get("confidence", 0)
            elements.append(Paragraph(
                f"{i}. {escape(path_str)} (確信度: {conf:.0%})",
                s["body"],
            ))
            desc = p.get("description", "")
            if desc:
                elements.append(Paragraph(f"　{escape(desc)}", s["body_small"]))
        elements.append(Spacer(1, 3 * mm))

    # Skill Timeline
    year_snapshots = payload.get("year_snapshots", [])
    if year_snapshots:
        elements.append(Paragraph("■ スキルタイムライン", s["section_header"]))

        all_skills = []
        seen = set()
        for snap in year_snapshots:
            for skill in snap.get("skills", []):
                if skill not in seen:
                    all_skills.append(skill)
                    seen.add(skill)

        years = [snap["year"] for snap in year_snapshots]
        skills_by_year = {snap["year"]: set(snap.get("skills", [])) for snap in year_snapshots}
        new_by_year = {snap["year"]: set(snap.get("new_skills", [])) for snap in year_snapshots}

        # Build table
        skill_col_w = 35 * mm
        year_col_w = (content_width - skill_col_w) / max(len(years), 1)

        header_row = [Paragraph("<b>スキル</b>", s["body_small"])]
        for y in years:
            header_row.append(Paragraph(f"<b>{y}</b>", s["body_small"]))

        data_rows = [header_row]
        for skill in all_skills:
            row = [Paragraph(escape(skill), s["body_small"])]
            for y in years:
                if skill in new_by_year.get(y, set()):
                    row.append(Paragraph("NEW", s["body_small"]))
                elif skill in skills_by_year.get(y, set()):
                    row.append(Paragraph("o", s["body_small"]))
                else:
                    row.append(Paragraph("", s["body_small"]))
            data_rows.append(row)

        col_widths = [skill_col_w] + [year_col_w] * len(years)
        timeline_table = Table(data_rows, colWidths=col_widths)
        timeline_table.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.3, TABLE_INNER),
            ("BOX", (0, 0), (-1, -1), 0.5, TABLE_BORDER),
            ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
            ("BACKGROUND", (0, 0), (0, -1), HEADER_BG),
            ("ALIGN", (1, 1), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("FONTNAME", (0, 0), (-1, -1), FONT_NAME),
            ("FONTSIZE", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ("LEFTPADDING", (0, 0), (-1, -1), 3),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ]))
        elements.append(timeline_table)

    doc.build(elements, onFirstPage=_add_page_number, onLaterPages=_add_page_number)
    buffer.seek(0)
    return buffer.getvalue()
