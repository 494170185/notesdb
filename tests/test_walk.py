"""M15 随机漫游测试。"""
from notesdb.links import build_graph
from notesdb.walk import walk


def _graph(**bodies):
    notes = {name: {"frontmatter": None, "body": body}
             for name, body in bodies.items()}
    return build_graph(notes), notes


def test_walk_returns_requested_steps():
    g, notes = _graph(a="[[b]]", b="[[c]]", c="[[a]]", d="", e="", f="")
    result = walk(g, notes, steps=3, seed=42)
    assert len(result) == 3


def test_walk_no_duplicates():
    g, notes = _graph(a="[[b]]", b="[[a]]", c="[[a]]")
    result = walk(g, notes, steps=10, seed=1)
    assert len(result) == len(set(result))


def test_walk_follows_edges():
    """漫游路径的每一步都应是链接相邻（或重新抽签）。"""
    g, notes = _graph(a="[[b]]", b="", c="", d="")
    result = walk(g, notes, steps=2, seed=7)
    if len(result) == 2:
        first, second = result
        adjacent = (second in g.outgoing.get(first, [])
                    or second in g.incoming.get(first, [])
                    or first in g.outgoing.get(second, []))
        # a-b 相邻；c/d 无边 → 重新抽签路径也允许
        assert adjacent or {first, second} <= {"c", "d"}


def test_walk_deterministic_with_seed():
    g, notes = _graph(a="[[b]]", b="[[c]]", c="", d="", e="")
    r1 = walk(g, notes, steps=3, seed=99)
    r2 = walk(g, notes, steps=3, seed=99)
    assert r1 == r2


def test_walk_empty_library():
    assert walk(build_graph({}), {}, steps=5) == []


def test_walk_zero_steps():
    g, notes = _graph(a="")
    assert walk(g, notes, steps=0) == []


def test_walk_isolated_notes_restart():
    """无链接库：漫游靠重新抽签，仍能凑满 steps。"""
    notes = {n: {"frontmatter": None, "body": ""} for n in "abcde"}
    g = build_graph(notes)
    result = walk(g, notes, steps=4, seed=3)
    assert len(result) == 4
