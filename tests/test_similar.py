"""M13 相似笔记测试。"""
import pytest

from notesdb.similar import (
    build_token_sets,
    note_token_set,
    similar_pairs,
    similar_to,
)


def _notes():
    return {
        "py1": {"frontmatter": None, "body": "python list dict comprehensions"},
        "py2": {"frontmatter": None, "body": "python dict set comprehensions"},
        "cook": {"frontmatter": None, "body": "煮面 加盐 水开 下面"},
        "cook2": {"frontmatter": None, "body": "煮饭 加盐 米 水开"},
        "misc": {"frontmatter": None, "body": "zzz qqq xxx"},
    }


def test_note_token_set_dedupes():
    ts = note_token_set({"body": "a a a b"})
    assert ts == {"a", "b"}


def test_build_token_sets_all_notes():
    ts = build_token_sets(_notes())
    assert set(ts) == {"py1", "py2", "cook", "cook2", "misc"}


def test_similar_pairs_sorted_desc():
    pairs = similar_pairs(_notes())
    sims = [s for _, _, s in pairs]
    assert sims == sorted(sims, reverse=True)


def test_similar_pairs_pair_ordering():
    """每对 (a, b) 保持 a < b 字典序，不重复。"""
    pairs = similar_pairs(_notes())
    keys = [(a, b) for a, b, _ in pairs]
    assert all(a < b for a, b in keys)
    assert len(keys) == len(set(keys))


def test_similar_topics_found():
    pairs = similar_pairs(_notes())
    names = {(a, b) for a, b, _ in pairs}
    assert ("py1", "py2") in names     # python 主题相似
    assert ("cook", "cook2") in names  # 做饭主题相似
    assert not any("misc" in k for k in names)  # 杂音不相似


def test_threshold_filters():
    """阈值调高后只剩最相似的对。"""
    strict = similar_pairs(_notes(), threshold=0.5)
    loose = similar_pairs(_notes(), threshold=0.1)
    assert len(strict) <= len(loose)


def test_top_limits_output():
    assert len(similar_pairs(_notes(), top=1)) == 1


def test_similar_to_returns_neighbors():
    neighbors = similar_to("py1", _notes())
    assert neighbors[0][0] == "py2"


def test_similar_to_respects_top():
    neighbors = similar_to("py1", _notes(), top=1)
    assert len(neighbors) <= 1


def test_similar_to_missing_raises():
    with pytest.raises(ValueError):
        similar_to("ghost", _notes())


def test_empty_library():
    assert similar_pairs({}) == []
