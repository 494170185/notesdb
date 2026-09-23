"""M39 重访建议测试。"""
import time

from notesdb.review import priority, stale, unreviewed_new


def _ts(days_ago: float) -> float:
    return time.time() - days_ago * 86400


def test_stale_finds_old():
    notes = {"old": {}, "new": {}}
    mt = {"old": _ts(120), "new": _ts(1)}
    out = stale(notes, lambda n: mt[n], days=90)
    assert [n for n, _ in out] == ["old"]
    assert out[0][1] >= 120


def test_stale_descending():
    notes = {"a": {}, "b": {}}
    mt = {"a": _ts(200), "b": _ts(100)}
    out = stale(notes, lambda n: mt[n], days=90)
    assert [n for n, _ in out] == ["a", "b"]


def test_stale_none():
    notes = {"a": {}}
    assert stale(notes, lambda _: _ts(1)) == []


def test_stale_ignores_unknown_mtime():
    assert stale({"a": {}}, lambda _: None) == []


def test_unreviewed_new():
    notes = {
        "fresh-island": {"body": "无链接"},
        "fresh-linked": {"body": "[[old]]"},
        "old": {"body": "无链接"},
    }
    mt = {"fresh-island": _ts(2), "fresh-linked": _ts(2), "old": _ts(30)}
    out = unreviewed_new(notes, lambda n: mt[n], created_days=7)
    assert out == ["fresh-island"]  # linked 有出链、old 超龄


def test_priority_scores_old_hubs_higher():
    notes = {
        "old-hub": {"body": ""},
        "old-leaf": {"body": ""},
        "young": {"body": ""},
    }
    for n in ("old-hub", "old-leaf"):
        notes[n]["body"] = ""
    # 三个引用者
    notes["r1"] = {"body": "[[old-hub]]"}
    notes["r2"] = {"body": "[[old-hub]]"}
    mt = {"old-hub": _ts(100), "old-leaf": _ts(100),
          "young": _ts(1), "r1": _ts(1), "r2": _ts(1)}
    out = priority(notes, lambda n: mt[n], top=3)
    assert out[0]["name"] == "old-hub"
    assert out[0]["backlinks"] == 2
    assert out[0]["score"] > out[1]["score"]


def test_priority_top_limit():
    notes = {n: {"body": ""} for n in "abcde"}
    mt = {n: _ts(50) for n in notes}
    assert len(priority(notes, lambda n: mt[n], top=2)) == 2
