"""M19 链接建议测试。"""
import pytest

from notesdb.suggest import (
    _edit_distance,
    suggest_backlink_targets,
    suggest_links,
)


def _notes():
    return {
        "py-list": {"frontmatter": None,
                    "body": "python list comprehension append extend sort"},
        "py-dict": {"frontmatter": None,
                    "body": "python dict comprehension keys values update"},
        "py-set": {"frontmatter": None,
                    "body": "python set comprehension union intersection"},
        "cook": {"frontmatter": None, "body": "煮面 水开 加盐"},
        "ref": {"frontmatter": None, "body": "看 [[py-list]] 与 [[py-dikt]]"},
    }


# ---------------------------------------------------------------- 编辑距离

def test_edit_distance_zero():
    assert _edit_distance("abc", "abc") == 0


def test_edit_distance_known_values():
    assert _edit_distance("kitten", "sitting") == 3
    assert _edit_distance("", "abc") == 3
    assert _edit_distance("abc", "") == 3


# ---------------------------------------------------------------- 链接建议

def test_suggest_links_finds_unlinked_similar():
    out = suggest_links("py-list", _notes())
    names = [n for n, _ in out]
    # py-dict/py-set 相似且未链接
    assert "py-dict" in names or "py-set" in names


def test_suggest_links_excludes_linked():
    # ref 已链接 py-list；且 cook 与 py-list 不相似
    out = suggest_links("ref", _notes())
    names = [n for n, _ in out]
    assert "py-list" not in names  # 已链接的不建议


def test_suggest_links_respects_top():
    out = suggest_links("py-list", _notes(), top=1)
    assert len(out) <= 1


def test_suggest_links_missing_raises():
    with pytest.raises(ValueError):
        suggest_links("ghost", _notes())


# ---------------------------------------------------------------- 悬空修复

def test_suggest_backlink_targets_fuzzy_match():
    """[[py-dikt]]（拼错）→ 建议改成 py-dict。"""
    out = suggest_backlink_targets("ref", _notes())
    assert len(out) == 1
    assert out[0]["dangling"] == "py-dikt"
    assert out[0]["best"]["name"] == "py-dict"
    assert out[0]["best"]["distance"] == 1


def test_suggest_backlink_targets_no_match():
    notes = {
        "a": {"frontmatter": None, "body": "[[zzzzzzzzzz]]"},
        "unrelated": {"frontmatter": None, "body": "内容"},
    }
    out = suggest_backlink_targets("a", notes)
    assert out[0]["best"] is None  # 没有相近名 → 建议新建


def test_suggest_backlink_targets_no_dangling():
    notes = {"a": {"frontmatter": None, "body": "[[a]]"}}
    assert suggest_backlink_targets("a", notes) == []
