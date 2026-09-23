"""大纲提取（M40）：从正文标题层级构建目录树。

导出页的 TOC、CLI 的 outline 命令共用。

  extract_outline(body)     [Heading]（层级/文本/行号，保序）
  render_toc(outline)       Markdown 缩进 TOC 文本
  max_depth(outline, n)     截断到前 n 级

h1 留给笔记名（render.py 同口径），正文的 # 视作一级。
"""
from __future__ import annotations

import re
from dataclasses import dataclass

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")


@dataclass
class Heading:
    level: int
    text: str
    line: int

    @property
    def anchor(self) -> str:
        """HTML 锚点 slug（导出页 href 用）。"""
        slug = re.sub(r"[^\w\u4e00-\u9fff]+", "-", self.text.lower()).strip("-")
        return slug


def extract_outline(body: str) -> list[Heading]:
    """正文的标题序列。"""
    out: list[Heading] = []
    for line_no, line in enumerate((body or "").splitlines()):
        m = _HEADING_RE.match(line)
        if m:
            out.append(Heading(level=len(m.group(1)),
                               text=m.group(2), line=line_no))
    return out


def render_toc(outline: list[Heading]) -> str:
    """Markdown 缩进 TOC。"""
    if not outline:
        return ""
    lines = []
    for h in outline:
        indent = "  " * (h.level - 1)
        lines.append(f"{indent}- {h.text}")
    return "\n".join(lines) + "\n"


def max_depth(outline: list[Heading], depth: int) -> list[Heading]:
    """截断到前 depth 级标题。"""
    return [h for h in outline if h.level <= depth]


def missing_levels(outline: list[Heading]) -> list[int]:
    """层级跳级检测（# 后直接 ###）：返回跳级发生处的行号。

  大纲层级应该渐深；跳级通常是排版失误。lint 的可选检查项。
    """
    jumps: list[int] = []
    prev = 0
    for h in outline:
        if h.level > prev + 1:
            jumps.append(h.line)
        prev = h.level
    return jumps
