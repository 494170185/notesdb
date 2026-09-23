"""链接建议（M19）：给笔记推荐"值得链接"的目标。

两类建议：
  suggest_links(name, notes)
    从笔记的相似笔记（M13）里挑出**尚未链接**的——
    "这两篇内容相关但你还没连"，这是双链笔记法的核心动作。

  suggest_backlink_targets(name, notes)
    悬空链接的修复建议：[[ghost]] 悬空时，找出库里名字与
    ghost 最相似（编辑距离）的现有笔记，提示改链或建新笔记。

建议只是建议：返回结构化数据，由 CLI/导出层展示，
不自动改写用户的笔记。
"""
from __future__ import annotations

from .links import build_graph
from .similar import similar_to

DEFAULT_TOP = 3
_MAX_EDIT_DISTANCE = 3  # 悬空修复建议的距离上限


def suggest_links(name: str, notes: dict[str, dict],
                  top: int = DEFAULT_TOP) -> list[tuple[str, float]]:
    """相似但未链接的笔记（降序）。已链接的（含悬空目标）剔除。"""
    if name not in notes:
        raise ValueError(f"笔记不存在: {name}")

    graph = build_graph(notes)
    already = set(graph.outgoing.get(name, []))
    already.add(name)  # 自己不算建议

    out: list[tuple[str, float]] = []
    for other, sim in similar_to(name, notes, top=top * 3):
        if other in already:
            continue
        out.append((other, sim))
        if len(out) >= top:
            break
    return out


def suggest_backlink_targets(name: str, notes: dict[str, dict]) -> list[dict]:
    """该笔记悬空链接的修复建议。

    返回 [{dangling, best: {name, distance} | None}]：
    best=None 表示库里没有相近名（建议新建笔记）。
    """
    if name not in notes:
        raise ValueError(f"笔记不存在: {name}")

    graph = build_graph(notes)
    my_targets = graph.outgoing.get(name, [])
    dangling = [t for t in my_targets if t not in notes]

    out = []
    for target in dangling:
        candidates = [(d, n) for n in notes
                      if (d := _edit_distance(target, n)) <= _MAX_EDIT_DISTANCE]
        best = min(candidates) if candidates else None
        out.append({
            "dangling": target,
            "best": {"name": best[1], "distance": best[0]} if best else None,
        })
    return out


def _edit_distance(a: str, b: str) -> int:
    """Levenshtein（O(len_a × len_b)，笔记名长度完全无压力）。"""
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(
                prev[j] + 1,        # 删除
                cur[j - 1] + 1,     # 插入
                prev[j - 1] + (ca != cb),  # 替换
            ))
        prev = cur
    return prev[-1]
