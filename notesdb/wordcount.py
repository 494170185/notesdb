"""字数与阅读时间（M31）：笔记的体量指标。

中文笔记的"字数"不是英文的 word count——汉字按字计、
英文按词计，混合时各自数再加总（与 tokenize 口径对齐但
不依赖索引：单字/单词粒度）。

  text_stats(body)        {chars, cjk_chars, words, lines}
  reading_minutes(body)   阅读时间（中文 400 字/分钟、英文 200 词/分钟，
                          混合按两类各自折算后相加）
  note_size_label(body)   体量标签：短/中/长（阅读 <1 分钟"短"，
                          1-3 分钟"中"，>3 分钟"长"）

导出页的 meta 区与 list 命令的消费入口。
"""
from __future__ import annotations

import re

_CJK_RE = re.compile(r"[\u4e00-\u9fff\u3400-\u4dbf]")
_WORD_RE = re.compile(r"[A-Za-z0-9]+(?:'[A-Za-z]+)*")

# 阅读速度（分钟/单位）——中文 400 字/分，英文 200 词/分
# 是常见排版基准（对比速读与儿童读物的折中）
_CJK_PER_MIN = 400
_WORDS_PER_MIN = 200


def text_stats(body: str) -> dict:
    """正文的体量统计。"""
    body = body or ""
    cjk = len(_CJK_RE.findall(body))
    words = len(_WORD_RE.findall(body))
    lines = body.count("\n") + (1 if body.strip() else 0)
    chars = len(body.strip())
    return {"chars": chars, "cjk_chars": cjk,
            "words": words, "lines": lines}


def reading_minutes(body: str) -> float:
    """阅读时间（分钟，向上取整到 0.5）。"""
    stats = text_stats(body)
    minutes = (stats["cjk_chars"] / _CJK_PER_MIN
               + stats["words"] / _WORDS_PER_MIN)
    import math

    return math.ceil(minutes * 2) / 2


def note_size_label(body: str) -> str:
    """体量标签（短/中/长）。"""
    minutes = reading_minutes(body)
    if minutes < 1:
        return "短"
    if minutes <= 3:
        return "中"
    return "长"
