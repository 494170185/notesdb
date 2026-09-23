"""时间分布（M24）：笔记的月度/周度产出统计。

回答"我哪段时间写得勤"：把时间线数据聚合成直方图。

  monthly(notes, mtime_fn) → [(月份, 数量)] 时间升序
  weekly(notes, mtime_fn)  → [(ISO 周, 数量)]
  hist_line(counts)        → 文本直方图（CLI 报表用）

每日笔记按名字日期（M11 同口径：日记名是权威），
普通笔记按 mtime。时间线语义与 daily.timeline 保持一致。
"""
from __future__ import annotations

from datetime import date, datetime, timedelta

from .daily import is_daily, parse_date


def _days(notes: dict[str, dict], mtime_fn) -> list[date]:
    """每篇笔记的归属日期（每日笔记用名字，其余用 mtime）。"""
    days: list[date] = []
    for name, note in notes.items():
        if is_daily(name):
            days.append(parse_date(name))
        else:
            ts = mtime_fn(name)
            if ts is not None:
                days.append(datetime.fromtimestamp(ts).date())
    return days


def monthly(notes: dict[str, dict], mtime_fn) -> list[tuple[str, int]]:
    """按月聚合：[("2026-09", n)]，时间升序、空月不补。"""
    counts: dict[str, int] = {}
    for d in _days(notes, mtime_fn):
        key = d.strftime("%Y-%m")
        counts[key] = counts.get(key, 0) + 1
    return sorted(counts.items())


def weekly(notes: dict[str, dict], mtime_fn) -> list[tuple[str, int]]:
    """按 ISO 周聚合：[("2026-W39", n)]。"""
    counts: dict[str, int] = {}
    for d in _days(notes, mtime_fn):
        iso_year, iso_week, _ = d.isocalendar()
        key = f"{iso_year}-W{iso_week:02d}"
        counts[key] = counts.get(key, 0) + 1
    return sorted(counts.items())


def active_streak_days(notes: dict[str, dict], mtime_fn) -> list[str]:
    """有笔记产出的日期（升序去重，供日历热图）。"""
    return sorted({d.isoformat() for d in _days(notes, mtime_fn)})


def hist_line(counts: list[tuple[str, int]], width: int = 20) -> str:
    """文本直方图：每行 "标签 ████ n"。"""
    if not counts:
        return ""
    peak = max(n for _, n in counts)
    lines = []
    for label, n in counts:
        bar = "█" * max(1, round(n / peak * width)) if peak else ""
        lines.append(f"{label} {bar} {n}")
    return "\n".join(lines)


def month_range(d: date) -> tuple[date, date]:
    """某月的第一天与最后一天（周统计的月份过滤用）。"""
    first = d.replace(day=1)
    if d.month == 12:
        next_first = d.replace(year=d.year + 1, month=1, day=1)
    else:
        next_first = d.replace(month=d.month + 1, day=1)
    return first, next_first - timedelta(days=1)
