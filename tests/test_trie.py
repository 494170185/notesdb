"""M37 前缀树测试。"""
from notesdb.trie import Trie, from_names


def test_insert_and_contains():
    t = Trie()
    t.insert("alpha")
    assert t.contains("alpha")
    assert not t.contains("alph")
    assert not t.contains("alpha2")


def test_prefix_relationship():
    t = Trie()
    t.insert("py")
    t.insert("python")
    assert t.contains("py") and t.contains("python")
    assert t.starts_with("py")


def test_empty_trie():
    t = Trie()
    assert not t.starts_with("x")
    assert t.complete("x") == []
    assert t.first_with("x") is None


def test_complete_sorted():
    t = from_names(["py-z", "py-a", "py-m", "other"])
    assert t.complete("py-") == ["py-a", "py-m", "py-z"]


def test_complete_limit():
    t = from_names([f"n{i:02d}" for i in range(50)])
    assert len(t.complete("n", limit=5)) == 5


def test_complete_exact_match_included():
    t = from_names(["py", "python"])
    assert t.complete("py") == ["py", "python"]


def test_first_with():
    t = from_names(["b1", "a2", "a3"])
    assert t.first_with("a") == "a2"


def test_len_counts_unique():
    t = Trie()
    t.insert("x")
    t.insert("x")  # 重复不计数
    assert len(t) == 1


def test_unicode_names():
    t = from_names(["笔记-甲", "笔记-乙"])
    assert t.complete("笔记-") == ["笔记-甲", "笔记-乙"]


def test_from_names_empty():
    assert len(from_names([])) == 0
