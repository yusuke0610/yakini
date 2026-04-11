from datetime import date
from typing import Any


def _to_date(value: Any) -> date | None:
    """値を date に変換する。str（YYYY-MM or YYYY-MM-DD）、date、None に対応。"""
    if value is None:
        return None
    if isinstance(value, date):
        return value
    if isinstance(value, str) and value:
        if len(value) == 7 and value[4] == "-":
            return date.fromisoformat(f"{value}-01")
        return date.fromisoformat(value)
    return None


def _get(item: Any, key: str) -> Any:
    """dict または ORM オブジェクトから値を取得する。"""
    if isinstance(item, dict):
        return item.get(key)
    return getattr(item, key, None)


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

    def sort_key(item: Any) -> tuple:
        end = _to_date(_get(item, end_key))
        start = _to_date(_get(item, start_key)) or date.min
        if end is None:
            return (0, date.max - start)
        return (1, date.max - end, date.max - start)

    return sorted(items, key=sort_key)


def sort_by_date_desc(
    items: list[Any],
    date_key: str = "acquired_date_value",
) -> list[Any]:
    """
    単一日付キーの降順でソートする（資格の取得日など）。
    日付が None の項目は最下位。安定ソート。
    """

    def sort_key(item: Any) -> tuple:
        item_date = _to_date(_get(item, date_key))
        if item_date is None:
            return (1,)
        return (0, date.max - item_date)

    return sorted(items, key=sort_key)


def sort_by_date_asc(
    items: list[Any],
    date_key: str = "occurred_on_value",
) -> list[Any]:
    """
    単一日付キーの昇順でソートする（履歴書の学歴・職歴など）。
    日付が None の項目は最下位。安定ソート。
    """

    def sort_key(item: Any) -> tuple:
        item_date = _to_date(_get(item, date_key))
        if item_date is None:
            return (1,)
        return (0, item_date)

    return sorted(items, key=sort_key)
