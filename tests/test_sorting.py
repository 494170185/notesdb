"""M25 排序测试。"""
from datetime import datetime

import pytest

from notesdb.sorting import (
    by_backlinks,
    by_mtime_desc,
    by_name,
    by_title,
    resolve_sort,
)


def _notes():
    return {
        "zeta": {"frontmatter": {"title": "Alpha"}, "body": ""},
        "alpha": {"frontmatter": None, "body": ""},
        "mid": {"frontmatter": {"title": "Beta"}, "body": ""},
    }


def test_by_name():
    assert by_name(_notes()) == ["alpha", "mid", "zeta"]


def test_by_title_uses_frontmatter_title():
    # 标题序：Alpha(zeta) < Beta(mid) < alpha（无标题回退名）
    assert by_title(_notes()) == ["zeta", "mid", "alpha"]


def test_by_mtime_desc():
    mt = {"alpha": 100.0, "mid": 300.0, "zeta": 200.0}
    assert by_mtime_desc(_notes(), lambda n: mt[n]) == ["mid", "zeta", "alpha"]


def test_by_mtime_desc_daily_uses_name():
    notes = {
        "2026-09-20": {"body": ""},
        "2026-09-01": {"body": ""},
        "normal": {"body": ""},
    }
    mt = {"normal": 1.0, "2026-09-20": 999.0, "2026-09-01": 999.0}
    out = by_mtime_desc(notes, lambda n: mt[n])
    # 每日笔记的日期 ordinal（>700k）远大于 epoch 1.0
    assert out[0] == "2026-09-20"
    assert out[-1] == "normal"


def test_by_mtime_desc_tie_broken_by_name():
    notes = {"b": {"body": ""}, "a": {"body": ""}}
    assert by_mtime_desc(notes, lambda _: 5.0) == ["a", "b"]


def test_by_mtime_desc_limit():
    mt = {"alpha": 100.0, "mid": 300.0, "zeta": 200.0}
    assert by_mtime_desc(_notes(), lambda n: mt[n], limit=1) == ["mid"]


def test_by_backlinks():
    notes = {
        "hub": {"body": ""},
        "a": {"body": "[[hub]]"},
        "b": {"body": ""},
    }
    assert by_backlinks(notes) == ["hub", "a", "b"]


def test_by_backlinks_tie_by_name():
    notes = {"x": {"body": ""}, "y": {"body": ""}}
    assert by_backlinks(notes) == ["x", "y"]


def test_resolve_sort_default():
    assert resolve_sort(None) == "name"


def test_resolve_sort_valid():
    for m in ("name", "title", "mtime", "backlinks"):
        assert resolve_sort(m) == m


def test_resolve_sort_invalid():
    with pytest.raises(ValueError, match="sort"):
        resolve_sort("random")
