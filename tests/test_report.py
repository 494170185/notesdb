"""M12 统计报表测试。"""
from notesdb.report import build_report, render_report


def _notes():
    return {
        "hub": {"frontmatter": None, "body": "枢纽 [[a]] [[b]] [[c]]"},
        "a": {"frontmatter": {"tags": ["x"]}, "body": "引用 [[hub]] 内容一"},
        "b": {"frontmatter": {"tags": ["x", "y"]}, "body": "引用 [[hub]] 内容二"},
        "c": {"frontmatter": {"tags": ["y"]}, "body": "也引用 [[hub]] 短"},
        "2026-09-24": {"frontmatter": None, "body": "每日笔记"},
        "lonely": {"frontmatter": None, "body": "孤岛"},
    }


def test_build_report_counts():
    r = build_report(_notes())
    assert r["notes"] == 6
    assert r["daily_notes"] == 1
    assert r["dangling"] == 0
    assert r["orphans"] == 2  # lonely 与 2026-09-24（每日笔记无链接）
    assert r["words"] > 0


def test_build_report_top_linked():
    r = build_report(_notes())
    # hub 被 a/b/c 三篇引用，排第一
    assert r["top_linked"][0]["name"] == "hub"
    assert r["top_linked"][0]["backlinks"] == 3


def test_build_report_top_tags_sorted():
    r = build_report(_notes())
    tags = [(t["tag"], t["count"]) for t in r["top_tags"]]
    assert tags[0] == ("x", 2) or tags[0] == ("y", 2)  # x/y 都是 2
    assert len(tags) == 2


def test_build_report_empty_library():
    r = build_report({})
    assert r["notes"] == 0
    assert r["top_tags"] == []
    assert r["top_linked"] == []


def test_render_report_markdown_readable():
    md = render_report(build_report(_notes()))
    assert "# 库统计报表" in md
    assert "hub" in md           # 枢纽出现
    assert "`x`" in md           # 标签出现
    assert "悬空 0" in md


def test_render_report_empty_library():
    md = render_report(build_report({}))
    assert "（无标签）" in md
    assert "（还没有链接关系）" in md
