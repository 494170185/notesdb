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
    t = Table(["name", "count"], [["a", 1], ["中文笔记", 22]])
    lines = t.render().splitlines()
    # 表头行与数据行的列起点对齐（用第二列起点位置验证）
    head_pos = lines[0].index("count")
    row2_pos = lines[3].index("22")
    assert head_pos == row2_pos


def test_table_render_has_separator():
    lines = Table(["a"], [["x"]]).render().splitlines()
    assert lines[1].startswith("---")


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
    assert out.splitlines()[-1].strip() == ""
