"""M24 时间分布测试。"""
from datetime import date, datetime

from notesdb.histogram import (
    active_streak_days,
    hist_line,
    month_range,
    monthly,
    weekly,
)


def _notes():
    return {
        "2026-09-01": {"frontmatter": None, "body": ""},
        "2026-09-20": {"frontmatter": None, "body": ""},
        "normal1": {"frontmatter": None, "body": "x"},   # mtime 定
    }


MT = {"normal1": datetime(2026, 9, 15, 10, 0).timestamp()}


def test_monthly_groups():
    out = monthly(_notes(), lambda n: MT.get(n))
    assert out == [("2026-09", 3)]


def test_monthly_spans_months():
    notes = {"2026-08-31": {"body": ""}, "2026-09-01": {"body": ""}}
    out = monthly(notes, lambda _: None)
    assert out == [("2026-08", 1), ("2026-09", 1)]


def test_monthly_ignores_no_timestamp():
    notes = {"ghost": {"body": ""}}
    assert monthly(notes, lambda _: None) == []


def test_weekly_iso_format():
    out = weekly(_notes(), lambda n: MT.get(n))
    # 2026-09-01 是周二（2026-W36）；09-15/20 是 W38/W39 前后
    assert len(out) >= 2
    assert all("-W" in k for k, _ in out)
    keys = [k for k, _ in out]
    assert keys == sorted(keys)


def test_weekly_empty():
    assert weekly({}, lambda _: None) == []


def test_active_streak_days_sorted_unique():
    days = active_streak_days(_notes(), lambda n: MT.get(n))
    assert days == ["2026-09-01", "2026-09-15", "2026-09-20"]


def test_hist_line_basic():
    lines = hist_line([("a", 4), ("b", 2)]).splitlines()
    assert len(lines) == 2
    assert "4" in lines[0] and "2" in lines[1]
    # a 的柱不短于 b
    assert len(lines[0]) >= len(lines[1])


def test_hist_line_empty():
    assert hist_line([]) == ""


def test_month_range():
    first, last = month_range(date(2026, 9, 24))
    assert (first.month, first.day) == (9, 1)
    assert (last.month, last.day) == (9, 30)
    first, last = month_range(date(2026, 12, 5))
    assert (last.month, last.day) == (12, 31)
