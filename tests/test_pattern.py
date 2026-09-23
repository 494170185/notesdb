"""M33 模式匹配测试。"""
import pytest

from notesdb.pattern import (
    compile_patterns,
    match_any,
    match_glob,
    match_regex,
    select,
)


def test_glob_basic():
    assert match_glob("draft-todo", "draft-*")
    assert not match_glob("final", "draft-*")


def test_glob_case_insensitive():
    assert match_glob("Draft-X", "draft-*")


def test_regex_search_semantics():
    assert match_regex("note-2026-09", r"2026-\d{2}")
    assert not match_regex("note-2025", r"2026")


def test_regex_bad_pattern_raises():
    with pytest.raises(ValueError, match="不合法"):
        match_regex("x", "[")


def test_match_any_glob():
    assert match_any("a-1", ["b-*", "a-*"])
    assert not match_any("c-1", ["a-*", "b-*"])


def test_match_any_empty_patterns():
    assert not match_any("x", [])


def test_match_any_bad_mode():
    with pytest.raises(ValueError, match="mode"):
        match_any("x", ["a"], "fuzzy")


def test_compile_patterns_dedupes_empty():
    assert len(compile_patterns(["", "a*"], "glob")) == 1


def test_compile_patterns_bad_regex_raises():
    with pytest.raises(ValueError, match="不合法"):
        compile_patterns(["["], "regex")


def test_select_glob():
    notes = {"draft-a": {}, "final-b": {}, "draft-c": {}}
    out = select(notes, ["draft-*"])
    assert set(out) == {"draft-a", "draft-c"}


def test_select_regex():
    notes = {"note-2026": {}, "note-2025": {}, "other": {}}
    out = select(notes, [r"\d{4}"], mode="regex")
    assert set(out) == {"note-2026", "note-2025"}


def test_select_empty_patterns_returns_all():
    notes = {"a": {}, "b": {}}
    assert select(notes, []) == notes


def test_select_none_match():
    assert select({"a": {}}, ["zzz-*"]) == {}
