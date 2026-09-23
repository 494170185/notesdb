"""终端 ANSI 高亮（M41）：CLI 里给搜索命中上色。

snippet.highlight 输出 HTML <mark>（导出用）；同一能力在
终端要 ANSI 转义。本模块做终端侧：

  ansi_highlight(text, terms)    词元命中处加 ANSI 黄底
  strip_ansi(text)               剥掉全部 ANSI 序列（管道/重定向安全）
  supports_color(stream)         终端是否支持彩色（NO_COLOR 环境变量尊重）

Windows 10+ 的终端原生支持 ANSI（cmd/PowerShell/Windows
Terminal 都行），不做旧版兼容垫层。
"""
from __future__ import annotations

import os
import re
import sys

# 黄底黑字
_HIGHLIGHT = "\x1b[7;33m"  # 反显+黄
_RESET = "\x1b[0m"

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def supports_color(stream=None) -> bool:
    """流是否应上色：非 TTY 或 NO_COLOR 时不上。"""
    stream = stream or sys.stdout
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    return hasattr(stream, "isatty") and stream.isatty()


def strip_ansi(text: str) -> str:
    """剥掉 ANSI 转义序列（输出到管道/文件前的清洗）。"""
    return _ANSI_RE.sub("", text)


def ansi_highlight(text: str, terms: list[str]) -> str:
    """词元命中处加反显黄色。词元化口径与索引一致。"""
    from .tokenize import tokenize

    tokens = sorted({t for term in terms for t in tokenize(term)},
                    key=len, reverse=True)
    if not tokens or not text:
        return text
    for token in tokens:
        pattern = re.escape(token)
        if token.isascii() and token[0].isalnum():
            pattern = r"(?<![A-Za-z0-9'])" + pattern + r"(?![A-Za-z0-9'])"
        text = re.sub(pattern, lambda m: _HIGHLIGHT + m.group(0) + _RESET,
                      text, flags=re.IGNORECASE)
    return text
