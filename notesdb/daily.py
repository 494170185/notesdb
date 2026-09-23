"""时间线视图（M11）：按日期组织的笔记访问层。

多数笔记工具的两大使用习惯都围绕日期：
  每日笔记（daily note）  "2026-09-24.md" 一个文件一天的流水
  时间线浏览             按创建/修改时间倒序回看笔记

本模块提供：
  is_daily(name) / parse_date(name)   日记名约定（YYYY-MM-DD.md）
  daily_name(date)                    日期 → 笔记名
  timeline(notes, mtime_fn)           修改时间倒序的时间线分组
  streak(notes, mtime_fn)             连续写笔记天数（习惯追踪）

mtime 来源由调用方注入（文件系统或测试替身）——笔记本身
不带修改时间（frontmatter 的 created 只是手写元数据，
与文件真实修改时间是两个东西）。
"""
from __future__ import annotations

import re
from datetime import date, timedelta

_DAILY_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def is_daily(name: str) -> bool:
    """笔记名是否符合每日笔记约定（YYYY-MM-DD）。"""
    if not _DAILY_RE.match(name or ""):
        return False
    try:
        parse_date(name)
        return True
    except ValueError:
        return False


def parse_date(name: str) -> date:
    """每日笔记名 → date。非约定名/非法日期抛 ValueError。"""
    m = _DAILY_RE.match(name or "")
    if not m:
        raise ValueError(f"不是每日笔记名: {name!r}")
    return date.fromisoformat(name)


def daily_name(d: date) -> str:
    """date → 每日笔记名。"""
    return d.isoformat()


def today_name() -> str:
    return daily_name(date.today())


def timeline(notes: dict[str, dict],
             mtime_fn) -> list[dict]:
    """修改时间倒序时间线。mtime_fn(name) → epoch 秒。

    返回 [{name, day: "YYYY-MM-DD"}]，按时间倒序。
    每日笔记按名字里的日期（而非 mtime）归组——日记回填
    时 mtime 与内容日期脱节，名字才是权威。
    """
    entries: list[tuple[str, str, float]] = []
    for name in notes:
        if is_daily(name):
            day = name
            ts = parse_date(name).toordinal()
        else:
            ts = mtime_fn(name)
            if ts is None:
                continue  # 没有时间信息的笔记进不了时间线
            day = _day_of(ts)
        entries.append((name, day, float(ts)))
    entries.sort(key=lambda x: -x[2])
    return [{"name": n, "day": d} for n, d, _ in entries]


def _day_of(ts: float) -> str:
    from datetime import datetime

    return datetime.fromtimestamp(ts).date().isoformat()


def streak(notes: dict[str, dict], mtime_fn,
           reference: date | None = None) -> int:
    """连续天数：从 reference（默认今天）往回数，每天都有笔记。

    每日笔记按名字算；普通笔记按 mtime 的日期算。
    今天的断档不中断 streak（今天还没写很正常）——
    从 reference 前一天开始连续才算。
    """
    ref = reference or date.today()

    # 有笔记的日期集合
    days: set[date] = set()
    for name in notes:
        if is_daily(name):
            days.add(parse_date(name))
        else:
            ts = mtime_fn(name)
            if ts is not None:
                from datetime import datetime
                days.add(datetime.fromtimestamp(ts).date())

    # 今天有 → 从今天起算；今天没有 → 从昨天起算（今日断档不中断）
    start = ref if ref in days else ref - timedelta(days=1)
    count = 0
    cur = start
    while cur in days:
        count += 1
        cur -= timedelta(days=1)
    return count
