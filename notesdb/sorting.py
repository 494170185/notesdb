"""笔记排序（M25）：list/导出用的多种排序策略。

  by_name          笔记名升序（默认，稳定可预期）
  by_title         标题升序（无标题回退笔记名）
  by_mtime_desc    修改时间倒序（最新的在前；每日笔记按名字日期）
  by_backlinks     被引数降序（知识枢纽优先）

多级排序：主键相同时按名字升序打破平局（保证顺序确定，
导出/测试可比对）。全部是纯函数：给定 notes（+可选 mtime_fn /
graph）返回排序后的名字列表。
"""
from __future__ import annotations

from .daily import is_daily, parse_date
from .links import LinkGraph, build_graph
from .model import note_title


def by_name(notes: dict[str, dict]) -> list[str]:
    return sorted(notes)


def by_title(notes: dict[str, dict]) -> list[str]:
    def key(name: str) -> tuple[str, str]:
        title = note_title(notes[name]) or name
        return (title, name)

    return sorted(notes, key=key)


def by_mtime_desc(notes: dict[str, dict], mtime_fn,
                  limit: int | None = None) -> list[str]:
    """最新在前。每日笔记用名字日期（回填日记 mtime 不权威）。"""
    def ts(name: str) -> float:
        if is_daily(name):
            return parse_date(name).toordinal()
        t = mtime_fn(name)
        return t if t is not None else 0.0

    names = sorted(notes, key=lambda n: (-ts(n), n))
    return names[:limit] if limit else names


def by_backlinks(notes: dict[str, dict],
                 graph: LinkGraph | None = None) -> list[str]:
    """被引最多的在前（知识枢纽优先）。"""
    g = graph or build_graph(notes)

    def key(name: str) -> tuple[int, str]:
        return (-len(g.backlinks(name)), name)

    return sorted(notes, key=key)


SORT_MODES = {
    "name": by_name,
    "title": by_title,
}


def resolve_sort(mode: str | None) -> str:
    """排序参数归一：非法值抛 ValueError（CLI 转 2 退出码）。"""
    if mode is None:
        return "name"
    if mode not in ("name", "title", "mtime", "backlinks"):
        raise ValueError(
            f"sort 只支持 name/title/mtime/backlinks，收到 {mode!r}")
    return mode
