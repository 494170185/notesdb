"""M11 每日笔记与时间线测试。"""
from datetime import date, datetime, timedelta

import pytest

from notesdb.daily import (
    daily_name,
    is_daily,
    parse_date,
    streak,
    timeline,
    today_name,
)


# ---------------------------------------------------------------- 命名约定

def test_is_daily_valid():
    assert is_daily("2026-09-24")


def test_is_daily_invalid():
    assert not is_daily("2026-9-24")     # 月份没补零
    assert not is_daily("笔记")
    assert not is_daily("2026-02-30")    # 非法日期
    assert not is_daily("")


def test_parse_date():
    assert parse_date("2026-01-02") == date(2026, 1, 2)


def test_parse_date_raises():
    with pytest.raises(ValueError):
        parse_date("notes")
    with pytest.raises(ValueError):
        parse_date("2026-13-01")


def test_daily_name_roundtrip():
    assert parse_date(daily_name(date(2026, 3, 5))) == date(2026, 3, 5)


def test_today_name_is_daily():
    assert is_daily(today_name())


# ---------------------------------------------------------------- 时间线

def test_timeline_sorted_desc():
    mt = {"a": 1000.0, "b": 2000.0}
    notes = {"a": {}, "b": {}}
    tl = timeline(notes, lambda n: mt[n])
    assert [e["name"] for e in tl] == ["b", "a"]


def test_timeline_daily_uses_name_date():
    """每日笔记按名字日期归组（回填日记 mtime 不权威）。"""
    mt = {"2026-09-20": 1000.0}  # 昨天写的，内容是 09-20
    notes = {"2026-09-20": {}}
    tl = timeline(notes, lambda n: mt[n])
    assert tl[0]["day"] == "2026-09-20"


def test_timeline_skips_unknown_mtime():
    notes = {"a": {}, "b": {}}
    tl = timeline(notes, lambda n: 1000.0 if n == "b" else None)
    assert [e["name"] for e in tl] == ["b"]


def test_timeline_day_of_normal_note():
    ts = datetime(2026, 9, 24, 10, 30).timestamp()
    notes = {"a": {}}
    tl = timeline(notes, lambda _: ts)
    assert tl[0]["day"] == "2026-09-24"


# ---------------------------------------------------------------- streak

def test_streak_counts_consecutive_daily():
    today = date(2026, 9, 24)
    notes = {}
    for i in range(3):
        d = today - timedelta(days=i)
        notes[daily_name(d)] = {}
    assert streak(notes, lambda _: None, reference=today) == 3


def test_streak_today_gap_does_not_break():
    """今天没写不中断（昨天前天连着算 2）。"""
    today = date(2026, 9, 24)
    notes = {
        daily_name(today - timedelta(days=1)): {},
        daily_name(today - timedelta(days=2)): {},
    }
    assert streak(notes, lambda _: None, reference=today) == 2


def test_streak_broken_by_gap():
    today = date(2026, 9, 24)
    notes = {
        daily_name(today): {},
        daily_name(today - timedelta(days=1)): {},
        daily_name(today - timedelta(days=3)): {},  # 中间断一天
    }
    assert streak(notes, lambda _: None, reference=today) == 2


def test_streak_empty_library():
    assert streak({}, lambda _: None) == 0


def test_streak_uses_mtime_for_normal_notes():
    today = date(2026, 9, 24)
    yesterday = datetime(2026, 9, 23, 12, 0).timestamp()
    day_before = datetime(2026, 9, 22, 12, 0).timestamp()
    mt = {"normal1": yesterday, "normal2": day_before}
    notes = {"normal1": {}, "normal2": {}}
    assert streak(notes, lambda n: mt[n], reference=today) == 2
