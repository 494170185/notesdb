"""M16 摘要与高亮测试。"""
from notesdb.snippet import highlight, snippet, snippets_for

BODY = "第一行\n第二行目标在这里\n第三行\n第四行\n第五行又目标\n"


# ---------------------------------------------------------------- snippet

def test_snippet_basic():
    s = snippet(BODY, 1)
    assert "第二行目标在这里" in s
    assert "第一行" in s and "第三行" in s  # 上下文


def test_snippet_context_zero():
    s = snippet(BODY, 1, context=0)
    assert s == "第二行目标在这里"


def test_snippet_near_edges():
    assert snippet(BODY, 0) == "第一行\n第二行目标在这里"
    assert snippet(BODY, 4).startswith("第四行")


def test_snippet_out_of_range():
    assert snippet(BODY, -1) == ""   # 标题哨兵值
    assert snippet(BODY, 99) == ""


# ---------------------------------------------------------------- snippets_for

def test_snippets_for_merges_adjacent():
    """相邻命中行合并为一段摘录。"""
    out = snippets_for(BODY, [1, 2])
    assert len(out) == 1
    assert "第二行" in out[0] and "第三行" in out[0]


def test_snippets_for_separate_groups():
    out = snippets_for(BODY, [1, 4], context=0)
    assert len(out) == 2
    assert out[0] == "第二行目标在这里"
    assert out[1] == "第五行又目标"


def test_snippets_for_limits_count():
    out = snippets_for(BODY, [0, 4], context=0, max_snippets=1)
    assert len(out) == 1


def test_snippets_for_ignores_title_sentinel():
    assert snippets_for(BODY, [-1, 1]) == snippets_for(BODY, [1])


def test_snippets_for_empty():
    assert snippets_for(BODY, []) == []


# ---------------------------------------------------------------- highlight

def test_highlight_english_word():
    out = highlight("the quick fox", ["quick"])
    assert "<mark>quick</mark>" in out


def test_highlight_case_insensitive():
    out = highlight("Python is fun", ["python"])
    assert "<mark>Python</mark>" in out


def test_highlight_chinese_bigram():
    out = highlight("全文检索", ["检索"])
    assert "<mark>检索</mark>" in out


def test_highlight_word_boundaries():
    """词元边界：cat 不高亮 category/cats 里的 cat 片段。"""
    out = highlight("category cats", ["cat"])
    assert out == "category cats"  # 都只作为更长词的一部分出现，不高亮


def test_highlight_word_boundaries_exact():
    out = highlight("a cat here", ["cat"])
    assert "<mark>cat</mark>" in out


def test_highlight_escapes_html():
    out = highlight("<b>xss</b>", ["xss"])
    assert "&lt;b&gt;" in out
    assert "<b>" not in out


def test_highlight_no_terms():
    assert highlight("plain <text>", []) == "plain &lt;text&gt;"


def test_highlight_multiple_terms():
    out = highlight("alpha beta", ["alpha", "beta"])
    assert "<mark>alpha</mark>" in out and "<mark>beta</mark>" in out


def test_highlight_empty_text():
    assert highlight("", ["x"]) == ""
