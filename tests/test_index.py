"""M3 分词与倒排索引测试。"""
from notesdb.index import InvertedIndex
from notesdb.tokenize import tokenize, tokenize_positions


# ---------------------------------------------------------------- 分词

def test_english_lowercase():
    assert tokenize("Hello WORLD") == ["hello", "world"]


def test_chinese_bigram():
    assert tokenize("笔记库") == ["笔记", "记库"]


def test_chinese_single_char():
    assert tokenize("字") == ["字"]


def test_mixed():
    assert tokenize("使用 notesdb 管理") == ["notesdb", "使用", "管理"]


def test_apostrophe_word():
    assert tokenize("don't") == ["don't"]


def test_punctuation_is_separator():
    assert tokenize("hello, world! 你好。") == ["hello", "world", "你好"]


def test_empty():
    assert tokenize("") == []
    assert tokenize(None) == []


def test_markdown_syntax_ignored():
    assert tokenize("# 标题 **加粗**") == ["标题", "加粗"]


def test_positions_sorted():
    pos = tokenize_positions("alpha 测试 beta")
    offsets = [o for _, o in pos]
    assert offsets == sorted(offsets)
    assert dict(pos)["测试"] == 6


# ---------------------------------------------------------------- 索引

def _idx_with(**bodies):
    idx = InvertedIndex()
    idx.build({name: {"frontmatter": None, "body": body}
               for name, body in bodies.items()})
    return idx


def test_search_word_hit():
    idx = _idx_with(a="hello world", b="world peace")
    hits = idx.search("world")
    assert set(hits) == {"a", "b"}


def test_search_case_insensitive():
    idx = _idx_with(a="PYTHON is great")
    assert set(idx.search("python")) == {"a"}


def test_search_chinese():
    idx = _idx_with(a="这是笔记库", b="另一个笔记")
    hits = idx.search("笔记")
    assert set(hits) == {"a", "b"}


def test_search_no_hit():
    idx = _idx_with(a="hello")
    assert idx.search("zebra") == {}


def test_search_title_indexed():
    idx = InvertedIndex()
    idx.build({"a": {"frontmatter": {"title": "数据库设计"},
                     "body": "正文没这个词"}})
    assert set(idx.search("数据库")) == {"a"}


def test_search_note_name_indexed():
    """无 title 时笔记名参与索引。"""
    idx = _idx_with(myproject="正文")
    assert set(idx.search("myproject")) == {"myproject"}


def test_search_multi_token_is_and():
    idx = _idx_with(a="hello world", b="hello only")
    assert set(idx.search("hello world")) == {"a"}


def test_search_prefix():
    idx = _idx_with(a="project alpha", b="projection", c="other")
    hits = idx.search_prefix("proj")
    assert set(hits) == {"a", "b"}


def test_search_phrase():
    idx = _idx_with(a="the quick brown fox", b="brown quick the")
    # "quick brown" 在 a 中相邻出现，在 b 中顺序颠倒
    assert set(idx.search_phrase("quick brown")) == {"a"}


def test_search_phrase_chinese():
    idx = _idx_with(a="全文检索很实用", b="检索全文很绕")
    assert set(idx.search_phrase("全文检索")) == {"a"}


def test_search_phrase_no_match():
    idx = _idx_with(a="hello world")
    assert idx.search_phrase("hello zebra") == {}


def test_stats():
    idx = _idx_with(a="one two", b="two three")
    stats = idx.stats()
    # 词元：one two three + 笔记名 a、b（无 title 时笔记名入索引）
    assert stats["vocabulary"] == 5
    assert stats["postings"] == 6  # one(a) two(a,b) three(b) a(标题) b(标题)


def test_rebuild_replaces():
    idx = _idx_with(a="old content")
    idx.build({"b": {"frontmatter": None, "body": "new content"}})
    assert idx.search("old") == {}
    assert set(idx.search("new")) == {"b"}
