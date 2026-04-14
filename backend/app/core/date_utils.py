from datetime import date, datetime, timedelta, timezone

# 日本標準時 (UTC+9)
JST = timezone(timedelta(hours=9))


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


def to_jst(dt: datetime) -> datetime:
    """UTC datetime を JST (UTC+9) に変換する。tzinfo なしの場合は UTC とみなす。"""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(JST)
