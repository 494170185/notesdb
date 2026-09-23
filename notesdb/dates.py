"""日期解析（M42）：frontmatter 日期字段的形态归一。

用户写日期的形态五花八门：ISO、斜杠、点分、中文年月日……
schema 校验只认 ISO（严格）；这里提供**宽容解析**用于展示层
（读得到就读，读不了的保持原样）：

  parse_flexible(s)        多形态解析 → date | None
  normalize_to_iso(s)      转成 ISO 字符串（失败原样返回）

支持形态：
  2026-09-24 / 2026/09/24 / 2026.09.24
  2026-9-4（不补零）
  2026年9月24日
  20260924（8 位连写）
  today / yesterday（相对词）
"""
from __future__ import annotations

import re
from datetime import date, timedelta

_ISO_RE = re.compile(r"^(\d{4})-(\d{1,2})-(\d{1,2})$")
_SLASH_RE = re.compile(r"^(\d{4})/(\d{1,2})/(\d{1,2})$")
_DOT_RE = re.compile(r"^(\d{4})\.(\d{1,2})\.(\d{1,2})$")
_CN_RE = re.compile(r"^(\d{4})年(\d{1,2})月(\d{1,2})日$")
_COMPACT_RE = re.compile(r"^(\d{4})(\d{2})(\d{2})$")


def parse_flexible(s) -> date | None:
    """多形态日期解析。解析不了返回 None（不抛——宽容口径）。"""
    if s is None:
        return None
    if isinstance(s, date):
        return s
    text = str(s).strip()
    if not text:
        return None
    low = text.lower()
    if low == "today":
        return date.today()
    if low == "yesterday":
        return date.today() - timedelta(days=1)
    for regex in (_ISO_RE, _SLASH_RE, _DOT_RE, _CN_RE):
        if m := regex.match(text):
            y, mo, d = (int(x) for x in m.groups())
            return _safe_date(y, mo, d)
    if m := _COMPACT_RE.match(text):
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        return _safe_date(y, mo, d)
    return None


def normalize_to_iso(s) -> str:
    """归一为 ISO 字符串；失败原样返回（str()）。"""
    d = parse_flexible(s)
    if d is None:
        return str(s) if s is not None else ""
    return d.isoformat()


def _safe_date(y: int, mo: int, d: int) -> date | None:
    try:
        return date(y, mo, d)
    except ValueError:
        return None
