"""M40 大纲测试。"""
from notesdb.outline import (
    Heading,
    extract_outline,
    max_depth,
    missing_levels,
    render_toc,
)


BODY = """\
# 一级
正文
## 二级A
### 三级
## 二级B
更多正文
#### 四级（跳级）
"""


def test_extract_outline_sequence():
    out = extract_outline(BODY)
    assert [(h.level, h.text) for h in out] == [
        (1, "一级"), (2, "二级A"), (3, "三级"),
        (2, "二级B"), (4, "四级（跳级）"),
    ]


def test_extract_outline_line_numbers():
    out = extract_outline(BODY)
    assert out[0].line == 0
    assert out[1].line == 2


def test_extract_ignores_non_heading():
    assert extract_outline("普通 #文本\n中 # 号") == []


def test_extract_empty():
    assert extract_outline("") == []


def test_render_toc_indents():
    toc = render_toc(extract_outline(BODY))
    lines = toc.strip().splitlines()
    assert lines[0] == "- 一级"
    assert lines[1] == "  - 二级A"
    assert lines[2] == "    - 三级"


def test_render_toc_empty():
    assert render_toc([]) == ""


def test_max_depth():
    out = max_depth(extract_outline(BODY), 2)
    assert all(h.level <= 2 for h in out)
    assert len(out) == 3


def test_missing_levels_detects_jump():
    jumps = missing_levels(extract_outline(BODY))
    assert jumps == [6]  # #### 四级（0 起第 6 行）直接跟在 ## 后


def test_missing_levels_clean():
    body = "# a\n## b\n## c\n# d\n"
    assert missing_levels(extract_outline(body)) == []


def test_heading_anchor():
    h = Heading(level=1, text="Hello 世界 & More!", line=0)
    a = h.anchor
    assert " " not in a and "!" not in a and "&" not in a
    assert "hello" in a and "世界" in a
