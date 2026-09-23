"""文本词元化（M3）：把正文切成可索引的词元。

中英混合笔记的检索口径：

- 英文/数字：连续字母数字串一个词元，小写化（大小写不敏感）；
- 中文：没有分词库依赖的前提下用 **bigram（二元切词）**——
  每两个相邻汉字组成一个词元。召回优于精确分词（不依赖词典、
  不会切错），代价是索引大一点，本地笔记库规模完全可接受；
  查询侧同样 bigram 化，"笔记" 命中所有含 "笔记" 二字连续出现
  的位置，这正是中文用户期望的行为；
- 分隔符（标点/空格/符号）：边界，不产生词元；
- Markdown 语法字符（#、*、` 等）天然属于分隔符，不特殊处理。

纯函数、无状态，索引与查询两侧共用同一实现（保证"怎么建
就怎么查"的一致性）。
"""
from __future__ import annotations

import re

# 英文/数字词（含撇号连字：it's, don't）
_WORD_RE = re.compile(r"[A-Za-z0-9]+(?:'[A-Za-z]+)*")


def tokenize(text: str) -> list[str]:
    """中英混合词元化。英文小写化，中文 bigram。"""
    if not text:
        return []
    tokens: list[str] = []

    def emit_word(m: re.Match) -> str:
        tokens.append(m.group(0).lower())
        return " "  # 占位，保持结构

    # 英文词先挖出（替换成空格避免与汉字粘连成 bigram）
    remainder = _WORD_RE.sub(emit_word, text)

    # 汉字连续段逐段 bigram
    for seg in _han_segments(remainder):
        for i in range(len(seg) - 1):
            tokens.append(seg[i:i + 2])
        if len(seg) == 1:
            tokens.append(seg)  # 单字自成词元
    return tokens


def _han_segments(text: str) -> list[str]:
    """提取全部连续汉字段。"""
    return re.findall(r"[\u4e00-\u9fff\u3400-\u4dbf]+", text)


def tokenize_positions(text: str) -> list[tuple[str, int]]:
    """带位置词元化：(词元, 字符偏移)。高亮需要偏移。"""
    out: list[tuple[str, int]] = []
    if not text:
        return out
    for m in _WORD_RE.finditer(text):
        out.append((m.group(0).lower(), m.start()))
    for seg_m in re.finditer(r"[\u4e00-\u9fff\u3400-\u4dbf]+", text):
        seg, start = seg_m.group(0), seg_m.start()
        for i in range(len(seg) - 1):
            out.append((seg[i:i + 2], start + i))
        if len(seg) == 1:
            out.append((seg, start))
    out.sort(key=lambda x: x[1])
    return out
