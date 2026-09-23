"""文本表格（M44）：CLI 的对齐表格输出。

  Table(headers, rows)     构建表格
  render()                 等宽对齐文本（中文按双宽计）
  render_markdown()        Markdown 管道表

中文对齐是老大难：等宽终端里 CJK 字符占 2 列。width()
用 Unicode East Asian Width 判定（W/F 宽，其余窄）。
"""
from __future__ import annotations

import unicodedata


def char_width(ch: str) -> int:
    """单字符显示宽度（CJK=2）。"""
    if unicodedata.east_asian_width(ch) in ("W", "F"):
        return 2
    return 1


def display_width(s: str) -> int:
    """字符串显示宽度。"""
    return sum(char_width(c) for c in s or "")


def pad(s: str, width: int) -> str:
    """按显示宽度右补空格。"""
    return s + " " * max(0, width - display_width(s))


class Table:
    """简单文本表格。"""

    def __init__(self, headers: list[str], rows: list[list]):
        self.headers = headers
        self.rows = rows

    def _columns(self) -> list[list[str]]:
        cols = [[str(h) for h in self.headers]]
        for row in self.rows:
            cols.append([str(c) if c is not None else "" for c in row])
        return cols

    def render(self) -> str:
        """等宽对齐（左对齐 + 双空格间隔）。"""
        cols = self._columns()
        n = len(self.headers)
        widths = [max(display_width(col[i]) for col in cols)
                  for i in range(n)]
        lines = []
        for r, col in enumerate(cols):
            line = "  ".join(pad(col[i], widths[i]) for i in range(n))
            lines.append(line.rstrip())
            if r == 0:
                lines.append("  ".join("-" * widths[i] for i in range(n)))
        return "\n".join(lines)

    def render_markdown(self) -> str:
        """Markdown 管道表。"""
        cols = self._columns()
        n = len(self.headers)
        out = ["| " + " | ".join(cols[0]) + " |",
               "| " + " | ".join("---" for _ in range(n)) + " |"]
        for col in cols[1:]:
            out.append("| " + " | ".join(col) + " |")
        return "\n".join(out)
