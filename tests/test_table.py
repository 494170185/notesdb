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
    # 第二列（count/1/22）的起始显示宽度在表头与数据行间一致
    starts = []
    for l in lines:
        token = l.rstrip().split()[-1]  # 行尾 token 即第二列
        starts.append(display_width(l) - display_width(token))
    # 表头、两行数据（跳过分隔行）
    assert starts[0] == starts[2] == starts[3]


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
