"""M4 标签体系测试。"""
from notesdb.tags import (
    build_tag_index,
    filter_by_tags,
    note_tags,
    tag_summary,
)


def _note(tags=None, **fm):
    front = {}
    if tags is not None:
        front["tags"] = tags
    front.update(fm)
    return {"frontmatter": front, "body": ""}


# ---------------------------------------------------------------- 读取

def test_tags_from_list():
    assert note_tags(_note(["Work", "project"])) == ["project", "work"]


def test_tags_from_comma_string():
    assert note_tags(_note("a, b ,c")) == ["a", "b", "c"]


def test_tags_single_value():
    assert note_tags(_note(42)) == ["42"]


def test_tags_none_when_missing():
    assert note_tags({"frontmatter": None, "body": ""}) == []


def test_tags_invalid_type_returns_empty():
    assert note_tags(_note({"nested": "map"})) == []


def test_tags_dedupe_case_insensitive():
    assert note_tags(_note(["Python", "python"])) == ["python"]


def test_tags_strip_and_skip_empty():
    assert note_tags(_note([" x ", "", "  "])) == ["x"]


# ---------------------------------------------------------------- 索引

def test_tag_index():
    notes = {"a": _note(["x"]), "b": _note(["x", "y"]), "c": _note(["y"])}
    idx = build_tag_index(notes)
    assert idx == {"x": ["a", "b"], "y": ["b", "c"]}


def test_tag_index_empty_lib():
    assert build_tag_index({}) == {}


# ---------------------------------------------------------------- 过滤

def test_filter_include_and_semantics():
    notes = {
        "a": _note(["x", "y"]),
        "b": _note(["x"]),
        "c": _note(["y"]),
    }
    out = filter_by_tags(notes, include=["x", "y"])
    assert list(out) == ["a"]


def test_filter_exclude():
    notes = {"a": _note(["x"]), "b": _note(["y"])}
    out = filter_by_tags(notes, exclude=["y"])
    assert list(out) == ["a"]


def test_filter_include_empty_means_all():
    notes = {"a": _note(["x"]), "b": _note(["y"])}
    assert list(filter_by_tags(notes)) == ["a", "b"]


def test_filter_case_insensitive_query():
    notes = {"a": _note(["Project"])}
    assert list(filter_by_tags(notes, include=["PROJECT"])) == ["a"]


def test_filter_combined():
    notes = {
        "a": _note(["work", "urgent"]),
        "b": _note(["work"]),
        "c": _note(["home", "urgent"]),
    }
    out = filter_by_tags(notes, include=["urgent"], exclude=["home"])
    assert list(out) == ["a"]


# ---------------------------------------------------------------- 统计

def test_tag_summary_sorted():
    notes = {
        "a": _note(["x"]), "b": _note(["x"]), "c": _note(["y"]),
    }
    s = tag_summary(notes)
    assert s == [{"tag": "x", "count": 2}, {"tag": "y", "count": 1}]
