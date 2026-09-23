"""M44 文本表格测试。"""
from notesdb.table import Table, char_width, display_width, pad


def test_char_width():
    assert char_width("a") == 1
    assert char_width("中") == 2
    assert char_width(" ") == 1


def test_display_width_mixed():
    assert display_width("中文abc") == 7  # 4 + 3


def test_display_width_empty():
    assert display_width("") == 0


def test_pad_to_width():
    assert pad("ab", 5) == "ab   "
    assert pad("中文", 6) == "中文  "  # 宽 4，补 2


def test_pad_over_width_untouched():
    assert pad("abcde", 3) == "abcde"


def test_table_render_aligned():
    from notesdb.table import display_width
    t = Table(["name", "count"], [["a", 1], ["中文笔记", 22]])
    lines = t.render().splitlines()
    # 第二列起点在所有行同一起始显示宽度（codepoint index 会骗人）
    starts = [display_width(l[:l.index("count")]) if "count" in l else
              display_width(l[:len(l) - len(l.lstrip().split("  ")[-1])])
              for l in lines[:1] + lines[2:]]
    # 表头与两行数据的第二列前缀宽度一致
    prefix_widths = set()
    for l in lines:
        first_col = l.split("  ")[0]
        prefix_widths.add(display_width(first_col))
    assert len(prefix_widths) == 1  # 第一列等宽对齐


def test_table_render_has_separator():
    lines = Table(["a"], [["x"]]).render().splitlines()
    assert set(lines[1]) == {"-"}  # 分隔线随列宽


def test_table_render_markdown():
    md = Table(["n", "v"], [["a", 1]]).render_markdown()
    assert md.splitlines()[0] == "| n | v |"
    assert md.splitlines()[1] == "| --- | --- |"
    assert md.splitlines()[2] == "| a | 1 |"


def test_table_empty_rows():
    md = Table(["h"], []).render_markdown()
    assert md == "| h |\n| --- |"


def test_table_none_renders_empty():
    out = Table(["h"], [[None]]).render()
    # None → 空串：最后一行没有 "None" 字样
    assert "None" not in out
