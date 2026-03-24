from datetime import date
from typing import Any


def _to_date(value: Any) -> date | None:
    """値を date に変換する。str（YYYY-MM or YYYY-MM-DD）、date、None に対応。"""
    if value is None:
        return None
    if isinstance(value, date):
        return value
    if isinstance(value, str) and value:
        # "YYYY-MM" → "YYYY-MM-01"
        if len(value) == 7 and value[4] == "-":
            return date.fromisoformat(f"{value}-01")
        return date.fromisoformat(value)
    return None


def sort_by_period_desc(
    items: list[Any],
    start_key: str = "start_date_value",
    end_key: str = "end_date_value",
) -> list[Any]:
    """
    在籍期間の降順でソートする。
    end が None（現在在籍中）の項目は常に最上位。
    同一 end 同士は start の降順。

    items は dict または ORM オブジェクト（属性アクセス）に対応する。
    日付フィールドは date 型・str 型（YYYY-MM / YYYY-MM-DD）のいずれにも対応。
    """
    def _get(item: Any, key: str) -> Any:
        if isinstance(item, dict):
            return item.get(key)
        return getattr(item, key, None)

    def sort_key(item: Any) -> tuple:
        end = _to_date(_get(item, end_key))
        start = _to_date(_get(item, start_key)) or date.min
        if end is None:
            # end_date が None → 最上位（0）、start_date 降順
            return (0, date.max - start)
        # end_date あり → (1, end_date 降順, start_date 降順)
        return (1, date.max - end, date.max - start)

    return sorted(items, key=sort_key)
