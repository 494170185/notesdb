"""随机漫游（M15）：沿链接图随机散步，重新发现沉睡的笔记。

用法场景：笔记库变大后大量旧笔记沉底。随机漫游给一个
"今天看看这几篇" 的入口：
  - walk(graph, notes, steps)：从随机笔记出发，每步随机跳到
    一篇出链/入链相邻笔记（无邻居时重新抽签起步）；
  - 有 seed 参数（测试可复现）；
  - 每篇最多访问一次（去重——漫游的意义是发现，不是重复）。

这是 Zettelkasten 社区的经典练习（Serendipity walk），
工程上就是带去重的随机游走。
"""
from __future__ import annotations

import random

from .links import LinkGraph


def walk(graph: LinkGraph, notes: dict[str, dict],
         steps: int = 5, seed: int | None = None) -> list[str]:
    """随机漫游返回访问序列（去重，最多 steps 篇）。"""
    if not notes or steps <= 0:
        return []
    rng = random.Random(seed)
    names = list(notes)

    visited: list[str] = []
    seen: set[str] = set()
    current = rng.choice(names)
    visited.append(current)
    seen.add(current)

    while len(visited) < steps:
        neighbors = _neighbors(graph, current, notes)
        # 过滤去过的；全去过就重新抽签
        fresh = [n for n in neighbors if n not in seen]
        if not fresh:
            unvisited = [n for n in names if n not in seen]
            if not unvisited:
                break  # 整库走完了
            current = rng.choice(unvisited)
        else:
            current = rng.choice(fresh)
        visited.append(current)
        seen.add(current)

    return visited


def _neighbors(graph: LinkGraph, name: str,
               notes: dict[str, dict]) -> list[str]:
    """链接图上的相邻笔记（出链 + 入链，只算存在的）。"""
    out = [t for t in graph.outgoing.get(name, []) if t in notes]
    incoming = [s for s in graph.incoming.get(name, []) if s in notes]
    return out + incoming
