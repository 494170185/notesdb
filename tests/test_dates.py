"""M42 日期解析测试。"""
from datetime import date

from notesdb.dates import normalize_to_iso, parse_flexible


def test_iso():
    assert parse_flexible("2026-09-24") == date(2026, 9, 24)


def test_slash_and_dot():
    assert parse_flexible("2026/9/4") == date(2026, 9, 4)
    assert parse_flexible("2026.09.24") == date(2026, 9, 24)


def test_chinese():
    assert parse_flexible("2026年9月24日") == date(2026, 9, 24)


def test_compact():
    assert parse_flexible("20260924") == date(2026, 9, 24)


def test_relative_words():
    assert parse_flexible("today") == date.today()
    assert parse_flexible("yesterday") == date.today().fromordinal(
        date.today().toordinal() - 1)


def test_invalid_returns_none():
    for bad in ("2026-13-01", "2026-02-30", "下周三", "", None, "2026"):
        assert parse_flexible(bad) is None


def test_date_object_passthrough():
    assert parse_flexible(date(2026, 1, 1)) == date(2026, 1, 1)


def test_normalize_success():
    assert normalize_to_iso("2026年9月24日") == "2026-09-24"
    assert normalize_to_iso("2026/9/4") == "2026-09-04"


def test_normalize_failure_keeps_original():
    assert normalize_to_iso("下周三") == "下周三"
    assert normalize_to_iso(None) == ""
