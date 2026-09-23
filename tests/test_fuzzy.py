"""M38 模糊匹配测试。"""
from notesdb.fuzzy import best_matches, jaro, jaro_winkler, levenshtein


# ---------------------------------------------------------------- levenshtein

def test_levenshtein_identical():
    assert levenshtein("abc", "abc") == 0


def test_levenshtein_known():
    assert levenshtein("kitten", "sitting") == 3
    assert levenshtein("flaw", "lawn") == 2


def test_levenshtein_empty():
    assert levenshtein("", "abc") == 3
    assert levenshtein("abc", "") == 3
    assert levenshtein("", "") == 0


def test_levenshtein_unicode():
    assert levenshtein("笔记", "笔记库") == 1


# ---------------------------------------------------------------- jaro

def test_jaro_identical():
    assert jaro("abc", "abc") == 1.0


def test_jaro_completely_different():
    assert jaro("abc", "xyz") == 0.0


def test_jaro_empty():
    assert jaro("", "x") == 0.0


def test_jaro_range():
    for a, b in (("dixon", "dicksonx"), ("martha", "marhta")):
        s = jaro(a, b)
        assert 0.0 <= s <= 1.0


# ---------------------------------------------------------------- jaro_winkler

def test_jw_prefix_boosts():
    """共同前缀提高分数：jw("note1", "note2") > jaro 部分。"""
    assert jaro_winkler("note1", "note2") > jaro("note1", "note2")


def test_jw_identical():
    assert jaro_winkler("same", "same") == 1.0


def test_jw_well_known_value():
    # 经典算例：martha/marhta ≈ 0.961
    assert abs(jaro_winkler("martha", "marhta") - 0.961) < 0.01


# ---------------------------------------------------------------- best_matches

def test_best_matches_ranks():
    out = best_matches("pythn", ["python", "java", "pthon"])
    assert out[0][0] in ("python", "pthon")
    assert out[-1][0] == "java"


def test_best_matches_limit():
    out = best_matches("x", ["a", "b", "c", "d"], n=2)
    assert len(out) == 2


def test_best_matches_empty_candidates():
    assert best_matches("x", []) == []


def test_best_matches_custom_scorer():
    out = best_matches("kitten", ["sitting", "x"], scorer=levenshtein)
    # 用编辑距离时分数是"越小越好"——排序仍降序，语义由调用方管
    assert len(out) == 2
