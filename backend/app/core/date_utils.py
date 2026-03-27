from datetime import date


def parse_iso_date(value: str) -> date:
    return date.fromisoformat(value)


def parse_year_month(value: str) -> date:
    return date.fromisoformat(f"{value}-01")


def format_iso_date(value: date | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()


def format_year_month(value: date | None) -> str | None:
    if value is None:
        return None
    return value.strftime("%Y-%m")
