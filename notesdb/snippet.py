"""搜索摘要与高亮（M16）：把命中行变成带上下文的可读片段。

query 返回行号列表；CLI/导出要展示"命中在哪、周围说了什么"：
  snippet(body, line_no, context=1)    单行命中的上下文摘录
  highlight(text, terms)               词元级 <mark> 高亮
  snippets_for(note, line_nos, ...)    多行命中的合并摘录（相邻行合段）

高亮的词元化口径与索引一致（tokenize），保证"搜得到的地方
一定高亮得出来"。HTML 转义先于 <mark> 注入（XSS 封死）。
"""
from __future__ import annotations

import html
import re

from .tokenize import tokenize

_MARK = "\x00{}\x01"  # 内部标记，转义后替换成 <mark>，避免二次转义


def snippet(body: str, line_no: int, context: int = 1) -> str:
    """第 line_no 行（0 起）的上下文摘录。

    越界行号（如标题的 -1）返回空串——调用方自行回退到标题。
    """
    lines = body.splitlines()
    if line_no < 0 or line_no >= len(lines):
        return ""
    lo = max(0, line_no - context)
    hi = min(len(lines), line_no + context + 1)
    return "\n".join(lines[lo:hi])


def snippets_for(body: str, line_nos: list[int], context: int = 1,
                 max_snippets: int = 3) -> list[str]:
    """多行命中的合并摘录：相邻（间隔 ≤ context*2+1）的行合为一段。"""
    valid = sorted(n for n in line_nos if n >= 0)
    if not valid:
        return []
    groups: list[list[int]] = [[valid[0]]]
    for n in valid[1:]:
        if n - groups[-1][-1] <= context * 2 + 1:
            groups[-1].append(n)
        else:
            groups.append([n])
    out = []
    for group in groups[:max_snippets]:
        lo = max(0, group[0] - context)
        hi = group[-1] + context + 1
        lines = body.splitlines()
        out.append("\n".join(lines[lo:hi]))
    return out


def highlight(text: str, terms: list[str]) -> str:
    """给文本里的词元加 <mark>。

    terms 先 tokenize（与索引同口径），在文本中按词元边界匹配。
    全部 HTML 转义后注入 <mark>——返回值可安全嵌入页面。
    """
    if not text:
        return ""
    tokens = sorted({t for term in terms for t in tokenize(term)},
                    key=len, reverse=True)
    if not tokens:
        return html.escape(text)

    escaped = html.escape(text)
    for token in tokens:
        # 只在词元边界替换：英文词元两侧不能是字母数字；
        # 中文 bigram 直接替换（汉字无边界概念）。
        # IGNORECASE：索引层词元已小写化，原文保持用户大小写。
        pattern = re.escape(token)
        if token.isascii() and token[0].isalnum():
            pattern = r"(?<![A-Za-z0-9'])" + pattern + r"(?![A-Za-z0-9'])"
        escaped = re.sub(
            pattern,
            lambda m: _MARK.format(m.group(0)),
            escaped, flags=re.IGNORECASE)
    return escaped.replace("\x00", "<mark>").replace("\x01", "</mark>")
