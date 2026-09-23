"""重访建议（M39）：找出最久没动的笔记，提醒回看。

笔记写了不看等于没写。三种"值得重访"：

  stale(notes, mtime_fn, days=90)   超过 N 天没修改的
  unreviewed_new(notes, mtime_fn, created_days=7)
                                     最近 N 天新建且一次都没被链接的
                                     （可能写完就忘）
  priority(notes, mtime_fn, top=5)  综合排序：越老且被引越多越优先
                                     （老 + 枢纽 = 值得先看）

mtime 注入（测试/真实文件系统皆可）。
"""
from __future__ import annotations

import time

from .links import build_graph


def _age_days(ts: float) -> float:
    return max(0.0, (time.time() - ts) / 86400)


def stale(notes: dict[str, dict], mtime_fn,
          days: float = 90) -> list[tuple[str, float]]:
    """超过 days 未修改的笔记 [(name, 天数)]（按天数降序）。"""
    out = []
    for name in notes:
        ts = mtime_fn(name)
        if ts is None:
            continue
        age = _age_days(ts)
        if age >= days:
            out.append((name, round(age, 1)))
    out.sort(key=lambda x: (-x[1], x[0]))
    return out


def unreviewed_new(notes: dict[str, dict], mtime_fn,
                   created_days: float = 7) -> list[str]:
    """新建不久且无任何链接关系的笔记（可能写完就忘）。"""
    graph = build_graph(notes)
    out = []
    for name in notes:
        ts = mtime_fn(name)
        if ts is None or _age_days(ts) > created_days:
            continue
        if not graph.outgoing.get(name) and not graph.incoming.get(name):
            out.append(name)
    return sorted(out)


def priority(notes: dict[str, dict], mtime_fn, top: int = 5) -> list[dict]:
    """重访优先级：age × (1 + backlinks/2) 评分，前 top 个。"""
    graph = build_graph(notes)
    scored = []
    for name in notes:
        ts = mtime_fn(name)
        if ts is None:
            continue
        age = _age_days(ts)
        backlinks = len(graph.backlinks(name))
        score = age * (1 + backlinks / 2)
        scored.append({"name": name, "age_days": round(age, 1),
                       "backlinks": backlinks, "score": round(score, 1)})
    scored.sort(key=lambda x: (-x["score"], x["name"]))
    return scored[:top]
