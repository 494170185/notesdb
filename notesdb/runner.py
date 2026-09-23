"""查询执行（M5）：Query × 笔记库 → 命中结果。

组合 index/tags/links 三个模块：每个查询条件先把候选集收窄，
全部条件 AND 串联。返回 {name: note}（保持原 dict 引用）。

run() 是唯一入口；CLI/导出/测试都走它。
"""
from __future__ import annotations

from .index import InvertedIndex
from .links import LinkGraph
from .query import Query
from .tags import filter_by_tags


def run(notes: dict[str, dict], q: Query,
        index: InvertedIndex | None = None,
        graph: LinkGraph | None = None) -> dict[str, dict]:
    """执行查询。index/graph 可注入（复用已构建的），None 则现场构建。"""
    if q.is_empty():
        return dict(notes)

    index = index or _build_index(notes)
    graph = graph or LinkGraph()
    if not graph.outgoing and not graph.incoming:
        from .links import build_graph
        graph = build_graph(notes)

    candidates: set[str] | None = None

    def narrow(names: set[str]) -> None:
        nonlocal candidates
        candidates = names if candidates is None else candidates & names

    # 全文词（AND）
    for word in q.words:
        narrow(set(index.search(word)))
    # 短语
    for phrase in q.phrases:
        narrow(set(index.search_phrase(phrase)))
    # 标签
    if q.include_tags or q.exclude_tags:
        narrow(set(filter_by_tags(notes, q.include_tags, q.exclude_tags)))
    # 链接到某笔记（出链侧）
    for target in q.links_to:
        narrow({name for name, targets in graph.outgoing.items()
                if target in targets})
    # 孤岛
    if q.orphan_only:
        narrow(set(graph.orphans(list(notes))))
    # 悬空链接
    if q.unresolved_only:
        unresolved_sources = set()
        for name, targets in graph.outgoing.items():
            if any(t not in notes for t in targets):
                unresolved_sources.add(name)
        narrow(unresolved_sources)

    if candidates is None:
        return dict(notes)
    return {name: notes[name] for name in notes if name in candidates}


def _build_index(notes: dict[str, dict]) -> InvertedIndex:
    idx = InvertedIndex()
    idx.build(notes)
    return idx
