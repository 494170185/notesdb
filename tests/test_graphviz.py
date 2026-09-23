"""M30 DOT 导出测试。"""
from notesdb.graphviz import _q, to_dot, write_dot


def _notes():
    return {
        "a": {"body": "[[b]] 与 [[ghost]]"},
        "b": {"body": "[[a]]"},
        "island": {"body": "孤岛"},
    }


def test_dot_structure():
    dot = to_dot(_notes())
    assert dot.startswith("digraph notesdb {")
    assert dot.rstrip().endswith("}")


def test_dot_edges():
    dot = to_dot(_notes())
    assert '"a" -> "b";' in dot
    assert '"b" -> "a";' in dot


def test_dangling_node_red_dashed():
    dot = to_dot(_notes())
    assert '"ghost" [label="ghost", color=red, style=dashed];' in dot
    assert '"a" -> "ghost" [color=red, style=dashed];' in dot


def test_island_node_boxed():
    dot = to_dot(_notes())
    assert "shape=box" in dot


def test_dot_escapes_quotes():
    dot = to_dot({'we"ird': {"body": ""}})
    assert '\\"' in dot  # 引号被转义


def test_q_helper():
    assert _q('a"b') == '"a\\"b"'
    assert _q("a\\b") == '"a\\\\b"'
    assert _q("plain") == '"plain"'


def test_write_dot_creates_file(tmp_path):
    path = write_dot(tmp_path, _notes())
    assert path.exists()
    assert "digraph" in path.read_text(encoding="utf-8")


def test_empty_library():
    dot = to_dot({})
    assert "digraph notesdb {" in dot
