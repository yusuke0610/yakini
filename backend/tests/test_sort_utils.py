from datetime import date

from app.services.shared.sort_utils import sort_by_date_asc, sort_by_date_desc, sort_by_period_desc


def _exp(start: str, end: str | None = None) -> dict:
    """テスト用の経歴 dict を生成する。"""
    return {
        "start_date_value": date.fromisoformat(f"{start}-01"),
        "end_date_value": date.fromisoformat(f"{end}-01") if end else None,
    }


def test_current_job_comes_first():
    """end_date が None（現在在籍中）の項目が最上位に来ること。"""
    items = [
        _exp("2020-01", "2022-06"),
        _exp("2023-01"),  # 現在在籍中
    ]
    result = sort_by_period_desc(items)
    assert result[0]["end_date_value"] is None
    assert result[1]["end_date_value"] is not None


def test_multiple_current_jobs_sorted_by_start_desc():
    """end_date が None の項目が複数ある場合、start_date DESC でソートされること。"""
    items = [
        _exp("2020-01"),
        _exp("2023-04"),
        _exp("2021-06"),
    ]
    result = sort_by_period_desc(items)
    starts = [item["start_date_value"] for item in result]
    assert starts == sorted(starts, reverse=True)


def test_end_date_desc():
    """end_date DESC でソートされること。"""
    items = [
        _exp("2018-01", "2020-03"),
        _exp("2020-04", "2023-12"),
        _exp("2015-01", "2019-06"),
    ]
    result = sort_by_period_desc(items)
    ends = [item["end_date_value"] for item in result]
    assert ends == sorted(ends, reverse=True)


def test_same_end_date_sorted_by_start_desc():
    """end_date が同一の場合、start_date DESC でソートされること。"""
    items = [
        _exp("2018-01", "2023-03"),
        _exp("2020-06", "2023-03"),
        _exp("2019-04", "2023-03"),
    ]
    result = sort_by_period_desc(items)
    starts = [item["start_date_value"] for item in result]
    assert starts == sorted(starts, reverse=True)


def test_empty_list():
    """空リストでエラーにならないこと。"""
    assert sort_by_period_desc([]) == []


def test_single_item():
    """要素が1つのリストでそのまま返ること。"""
    items = [_exp("2023-01", "2024-01")]
    result = sort_by_period_desc(items)
    assert len(result) == 1
    assert result[0] is items[0]


def test_with_string_dates():
    """文字列日付（YYYY-MM）にも対応すること。"""
    items = [
        {"start_date": "2018-01", "end_date": "2020-03"},
        {"start_date": "2023-01", "end_date": None},
        {"start_date": "2020-04", "end_date": "2023-12"},
    ]
    result = sort_by_period_desc(items, start_key="start_date", end_key="end_date")
    # 現在在籍中が最上位
    assert result[0]["end_date"] is None
    # 次に end_date が新しい順
    assert result[1]["end_date"] == "2023-12"
    assert result[2]["end_date"] == "2020-03"


def test_mixed_scenario():
    """現在在籍中 + 退職済みの混在ケース。"""
    items = [
        _exp("2015-01", "2018-06"),
        _exp("2023-01"),           # 現在在籍中
        _exp("2018-07", "2020-12"),
        _exp("2021-01"),           # 現在在籍中
        _exp("2020-01", "2022-03"),
    ]
    result = sort_by_period_desc(items)
    # 現在在籍中が上位2件（start_date DESC）
    assert result[0]["start_date_value"] == date(2023, 1, 1)
    assert result[0]["end_date_value"] is None
    assert result[1]["start_date_value"] == date(2021, 1, 1)
    assert result[1]["end_date_value"] is None
    # 退職済みは end_date DESC
    assert result[2]["end_date_value"] == date(2022, 3, 1)
    assert result[3]["end_date_value"] == date(2020, 12, 1)
    assert result[4]["end_date_value"] == date(2018, 6, 1)


# ===== sort_by_date_desc テスト =====


def _qual(acquired: str | None) -> dict:
    """テスト用の資格 dict を生成する。"""
    return {
        "acquired_date_value": date.fromisoformat(acquired) if acquired else None,
        "name": f"資格_{acquired}",
    }


def test_date_desc_sorted():
    """日付降順でソートされること。"""
    items = [_qual("2020-01-15"), _qual("2023-06-01"), _qual("2021-03-10")]
    result = sort_by_date_desc(items)
    dates = [item["acquired_date_value"] for item in result]
    assert dates == sorted(dates, reverse=True)


def test_date_desc_none_last():
    """日付が None の項目が最下位に来ること。"""
    items = [_qual(None), _qual("2023-06-01"), _qual("2020-01-15")]
    result = sort_by_date_desc(items)
    assert result[-1]["acquired_date_value"] is None
    assert result[0]["acquired_date_value"] == date(2023, 6, 1)


def test_date_desc_stable():
    """日付が同一の項目の順序が維持されること（安定ソート）。"""
    items = [
        {"acquired_date_value": date(2023, 1, 1), "name": "A"},
        {"acquired_date_value": date(2023, 1, 1), "name": "B"},
        {"acquired_date_value": date(2023, 1, 1), "name": "C"},
    ]
    result = sort_by_date_desc(items)
    names = [item["name"] for item in result]
    assert names == ["A", "B", "C"]


def test_date_desc_empty():
    """空リストでエラーにならないこと。"""
    assert sort_by_date_desc([]) == []


def test_date_desc_with_string_dates():
    """文字列日付にも対応すること。"""
    items = [
        {"date": "2020-03-15", "name": "A"},
        {"date": "2023-06-01", "name": "B"},
    ]
    result = sort_by_date_desc(items, date_key="date")
    assert result[0]["name"] == "B"
    assert result[1]["name"] == "A"


# ===== sort_by_date_asc テスト =====


def _history(occurred: str | None) -> dict:
    """テスト用の学歴/職歴 dict を生成する。"""
    return {
        "occurred_on_value": date.fromisoformat(f"{occurred}-01") if occurred else None,
        "name": f"項目_{occurred}",
    }


def test_date_asc_sorted():
    """日付昇順でソートされること。"""
    items = [_history("2020-03"), _history("2015-04"), _history("2018-03")]
    result = sort_by_date_asc(items)
    dates = [item["occurred_on_value"] for item in result]
    assert dates == sorted(dates)


def test_date_asc_none_last():
    """日付が None の項目が最下位に来ること。"""
    items = [_history(None), _history("2020-03"), _history("2015-04")]
    result = sort_by_date_asc(items)
    assert result[-1]["occurred_on_value"] is None
    assert result[0]["occurred_on_value"] == date(2015, 4, 1)


def test_date_asc_multiple_none_stable():
    """None が複数ある場合、元の順序が維持されること。"""
    items = [
        {"occurred_on_value": None, "name": "A"},
        {"occurred_on_value": date(2020, 1, 1), "name": "B"},
        {"occurred_on_value": None, "name": "C"},
    ]
    result = sort_by_date_asc(items)
    assert result[0]["name"] == "B"
    # None 同士は元の順序を維持
    assert result[1]["name"] == "A"
    assert result[2]["name"] == "C"


def test_date_asc_stable():
    """日付が同一の項目の順序が維持されること（安定ソート）。"""
    items = [
        {"occurred_on_value": date(2020, 4, 1), "name": "A"},
        {"occurred_on_value": date(2020, 4, 1), "name": "B"},
        {"occurred_on_value": date(2020, 4, 1), "name": "C"},
    ]
    result = sort_by_date_asc(items)
    names = [item["name"] for item in result]
    assert names == ["A", "B", "C"]


def test_date_asc_empty():
    """空リストでエラーにならないこと。"""
    assert sort_by_date_asc([]) == []


def test_date_asc_with_string_dates():
    """文字列日付にも対応すること。"""
    items = [
        {"date": "2020-03", "name": "A"},
        {"date": "2015-04", "name": "B"},
    ]
    result = sort_by_date_asc(items, date_key="date")
    assert result[0]["name"] == "B"
    assert result[1]["name"] == "A"
