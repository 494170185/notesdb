"""M2 wikilink 与链接图测试。"""
from notesdb.links import (
    build_graph,
    extract_wikilinks,
    extract_wikilinks_ignoring_code,
)

# ---------------------------------------------------------------- 提取

def test_basic_wikilink():
    assert extract_wikilinks("see [[Target]] here") == ["Target"]


def test_alias_form():
    assert extract_wikilinks("[[Target|显示名]]") == ["Target"]


def test_multiple_in_order_with_duplicates():
    links = extract_wikilinks("[[A]] mid [[B]] again [[A]]")
    assert links == ["A", "B", "A"]


def test_no_link_in_plain_text():
    assert extract_wikilinks("普通文本 [单括号] [[ [不完整") == []


def test_multiline_target_rejected():
    assert extract_wikilinks("[[Tar\nget]]") == []


def test_code_block_ignored():
    body = "text [[Real]]\n```\n[[Fake]]\n```\nafter [[Also Real]]\n"
    assert extract_wikilinks_ignoring_code(body) == ["Real", "Also Real"]


def test_tilde_fence_ignored():
    body = "~~~\n[[Fake]]\n~~~\n[[Real]]\n"
    assert extract_wikilinks_ignoring_code(body) == ["Real"]


def test_inline_code_ignored():
    assert extract_wikilinks_ignoring_code("run `[[cmd]]` now [[Real]]") == ["Real"]


def test_unclosed_fence_treats_rest_as_code():
    """没闭合的围栏：后续都是代码（与 CommonMark 一致）。"""
    body = "[[A]]\n```\n[[B]]\n"
    assert extract_wikilinks_ignoring_code(body) == ["A"]


# ---------------------------------------------------------------- 链接图

def _notes(**bodies):
    return {name: {"frontmatter": None, "body": body}
            for name, body in bodies.items()}


def test_graph_outgoing_and_incoming():
    g = build_graph(_notes(a="link to [[b]]", b="link to [[a]] and [[c]]"))
    assert g.outgoing["a"] == ["b"]
    assert set(g.outgoing["b"]) == {"a", "c"}
    assert g.backlinks("a") == ["b"]
    assert g.backlinks("b") == ["a"]


def test_graph_unresolved():
    g = build_graph(_notes(a="[[ghost]] and [[phantom]]", b="[[ghost]]"))
    assert g.unresolved == ["ghost", "phantom"]


def test_graph_duplicate_links_deduped():
    g = build_graph(_notes(a="[[b]] [[b]] [[b]]", b="content"))
    assert g.outgoing["a"] == ["b"]
    assert g.backlinks("b") == ["a"]


def test_graph_dangling_target_has_no_backlinks():
    """悬空目标（库中不存在）不进 incoming——没笔记可挂。"""
    g = build_graph(_notes(a="[[ghost]]"))
    assert g.outgoing["a"] == ["ghost"]
    assert g.backlinks("ghost") == []
    assert g.unresolved == ["ghost"]


def test_graph_self_link():
    g = build_graph(_notes(a="self [[a]]"))
    assert g.outgoing["a"] == ["a"]
    assert g.backlinks("a") == ["a"]


def test_graph_orphans():
    g = build_graph(_notes(a="[[b]]", b="", c="", d="[[a]]"))
    assert g.orphans(["a", "b", "c", "d"]) == ["c"]


def test_graph_code_links_not_counted():
    g = build_graph(_notes(a="```\n[[b]]\n```"))
    assert g.outgoing["a"] == []
    assert g.backlinks("b") == []
