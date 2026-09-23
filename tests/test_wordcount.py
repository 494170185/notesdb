"""M31 字数与阅读时间测试。"""
from notesdb.wordcount import (
    note_size_label,
    reading_minutes,
    text_stats,
)


def test_text_stats_pure_chinese():
    s = text_stats("这是五个字的内容")  # 8 个汉字
    assert s["cjk_chars"] == 8
    assert s["words"] == 0


def test_text_stats_pure_english():
    s = text_stats("hello world")
    assert s["words"] == 2
    assert s["cjk_chars"] == 0


def test_text_stats_mixed():
    s = text_stats("使用 notesdb 工具")
    assert s["cjk_chars"] == 4  # 使用 + 工具
    assert s["words"] == 1


def test_text_stats_empty():
    s = text_stats("")
    assert s == {"chars": 0, "cjk_chars": 0, "words": 0, "lines": 0}


def test_text_stats_lines():
    assert text_stats("a\nb\nc")["lines"] == 3


def test_reading_minutes_short():
    # 有内容即至少 0.5 分钟（ceil 到半分钟档）
    assert reading_minutes("短文") == 0.5
    assert reading_minutes("") == 0.0


def test_reading_minutes_half_step():
    # 200 汉字 = 0.5 分钟（400/分钟）
    assert reading_minutes("字" * 200) == 0.5


def test_reading_minutes_english():
    # 200 词 = 1 分钟
    assert reading_minutes(" ".join(["w"] * 200)) == 1.0


def test_reading_minutes_mixed_additive():
    # 200 字（0.5min）+ 100 词（0.5min）= 1.0
    text = "字" * 200 + " " + " ".join(["w"] * 100)
    assert reading_minutes(text) == 1.0


def test_size_labels():
    assert note_size_label("短") == "短"
    assert note_size_label("字" * 800) == "中"     # 2 分钟
    assert note_size_label("字" * 2000) == "长"    # 5 分钟
