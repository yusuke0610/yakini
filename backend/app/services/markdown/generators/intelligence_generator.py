from typing import Any

from ..templates import intelligence_template as tpl
from ..utils.markdown_utils import field_line


def build_intelligence_markdown(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append(tpl.TITLE)
    lines.append("")

    # Overview
    lines.append(tpl.SECTION_OVERVIEW)
    lines.append("")
    lines.append(field_line("ユーザー", payload.get("username", "")))
    lines.append(field_line("分析リポジトリ数", str(payload.get("repos_analyzed", 0))))
    lines.append(field_line("ユニークスキル数", str(payload.get("unique_skills", 0))))
    lines.append(field_line("分析日時", payload.get("analyzed_at", "")))
    lines.append("")

    # AI Summary
    summary = payload.get("summary", "")
    if summary:
        lines.append(tpl.SECTION_AI_SUMMARY)
        lines.append("")
        lines.append(summary)
        lines.append("")

    # Skill Timeline
    year_snapshots = payload.get("year_snapshots", [])
    if year_snapshots:
        lines.append(tpl.SECTION_SKILL_TIMELINE)
        lines.append("")

        all_skills = []
        seen = set()
        for s in year_snapshots:
            for skill in s.get("skills", []):
                if skill not in seen:
                    all_skills.append(skill)
                    seen.add(skill)

        years = [s["year"] for s in year_snapshots]
        skills_by_year = {s["year"]: set(s.get("skills", [])) for s in year_snapshots}
        new_by_year = {s["year"]: set(s.get("new_skills", [])) for s in year_snapshots}

        # Table header
        header = "| スキル | " + " | ".join(years) + " |"
        separator = "|---|" + "|".join(["---"] * len(years)) + "|"
        lines.append(header)
        lines.append(separator)

        for skill in all_skills:
            cells = []
            for y in years:
                if skill in new_by_year.get(y, set()):
                    cells.append("NEW")
                elif skill in skills_by_year.get(y, set()):
                    cells.append("o")
                else:
                    cells.append("")
            lines.append(f"| {skill} | " + " | ".join(cells) + " |")
        lines.append("")

    # Growth Trends
    growth = payload.get("growth", [])
    if growth:
        lines.append(tpl.SECTION_GROWTH_TRENDS)
        lines.append("")

        emerging = [g for g in growth if g.get("trend") in ("emerging", "new")]
        stable = [g for g in growth if g.get("trend") == "stable"]
        declining = [g for g in growth if g.get("trend") == "declining"]

        if emerging:
            lines.append("### Emerging / New")
            lines.append("")
            for g in emerging:
                v = g.get("velocity", 0)
                sign = "+" if v > 0 else ""
                lines.append(f"- {g['skill_name']} ({sign}{v:.1f})")
            lines.append("")

        if stable:
            lines.append("### Stable")
            lines.append("")
            for g in stable:
                lines.append(f"- {g['skill_name']} ({g.get('velocity', 0):.1f})")
            lines.append("")

        if declining:
            lines.append("### Declining")
            lines.append("")
            for g in declining:
                lines.append(f"- {g['skill_name']} ({g.get('velocity', 0):.1f})")
            lines.append("")

    # Career Prediction
    prediction = payload.get("prediction", {})
    if prediction:
        lines.append(tpl.SECTION_CAREER_PREDICTION)
        lines.append("")

        current = prediction.get("current_role", {})
        if current:
            conf = current.get("confidence", 0)
            lines.append(f"### 現在のロール: {current.get('role_name', '')} ({conf:.0%})")
            lines.append("")
            matching = current.get("matching_skills", [])
            if matching:
                lines.append(field_line("マッチするスキル", ", ".join(matching)))
            missing = current.get("missing_skills", [])
            if missing:
                lines.append(field_line("不足スキル", ", ".join(missing)))
            lines.append("")

        next_roles = prediction.get("next_roles", [])
        if next_roles:
            lines.append("### 次のキャリアステップ")
            lines.append("")
            for role in next_roles:
                conf = role.get("confidence", 0)
                lines.append(f"- **{role.get('role_name', '')}** ({conf:.0%})")
                missing = role.get("missing_skills", [])
                if missing:
                    lines.append(f"  - 不足スキル: {', '.join(missing)}")
            lines.append("")

        long_term = prediction.get("long_term_roles", [])
        if long_term:
            lines.append("### 長期キャリア候補")
            lines.append("")
            for role in long_term:
                conf = role.get("confidence", 0)
                lines.append(f"- **{role.get('role_name', '')}** ({conf:.0%})")
            lines.append("")

    # Career Simulation
    simulation = payload.get("simulation", {})
    paths = simulation.get("paths", [])
    if paths:
        lines.append(tpl.SECTION_CAREER_SIMULATION)
        lines.append("")
        for i, p in enumerate(paths, 1):
            path_str = " -> ".join(p.get("path", []))
            conf = p.get("confidence", 0)
            lines.append(f"{i}. {path_str} ({conf:.0%})")
            desc = p.get("description", "")
            if desc:
                lines.append(f"   {desc}")
        lines.append("")

    return "\n".join(lines)
