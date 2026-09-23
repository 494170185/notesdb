"""CLI 入口（M5）：python -m notesdb <命令>。

命令：
  list                  列出全部笔记（名/标题/标签）
  query '<查询串>'      执行查询（语法见 query 模块）
  tags                  标签使用统计
  links                 链接图摘要（悬空/孤岛/backlink 计数）
  stats                 库统计（笔记数/词汇量/链接数）

全部只读。写入（编辑/重命名）走后续里程碑。
"""
from __future__ import annotations

import argparse
import sys

from . import __version__
from .links import build_graph
from .model import note_title
from .query import QueryError, parse_query
from .runner import run
from .store import Store
from .tags import note_tags, tag_summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="notesdb", description="本地 Markdown 笔记库工具")
    parser.add_argument("--version", action="store_true")
    parser.add_argument("--root", default=".", help="笔记库根目录")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("list", help="列出全部笔记")
    p_query = sub.add_parser("query", help="执行查询")
    p_query.add_argument("query_string", help="查询串（见 query 模块语法）")
    sub.add_parser("tags", help="标签使用统计")
    sub.add_parser("links", help="链接图摘要")
    sub.add_parser("stats", help="库统计")
    return parser


def _load(root: str):
    notes, errors = Store(root).load()
    for e in errors:
        print(f"⚠️  {e}", file=sys.stderr)
    return notes


def main(argv: list[str] | None = None) -> int:
    ns = _parse(argv)

    if ns.version:
        print(__version__)
        return 0

    notes = _load(ns.root)

    if ns.command == "list":
        for name in sorted(notes):
            note = notes[name]
            title = note_title(note) or ""
            tags = ",".join(note_tags(note))
            line = name + (f"  |  {title}" if title else "")
            if tags:
                line += f"  [{tags}]"
            print(line)
        return 0

    if ns.command == "query":
        try:
            q = parse_query(ns.query_string)
        except QueryError as e:
            print(f"查询语法错误: {e}", file=sys.stderr)
            return 2
        hits = run(notes, q)
        print(f"命中 {len(hits)}/{len(notes)}")
        for name in sorted(hits):
            print(f"  {name}")
        return 0

    if ns.command == "tags":
        for item in tag_summary(notes):
            print(f"{item['count']:4d}  {item['tag']}")
        return 0

    if ns.command == "links":
        graph = build_graph(notes)
        print(f"悬空链接 {len(graph.unresolved)}: "
              + ", ".join(graph.unresolved[:10])
              + ("…" if len(graph.unresolved) > 10 else ""))
        orphans = graph.orphans(list(notes))
        print(f"孤岛笔记 {len(orphans)}: " + ", ".join(orphans[:10])
              + ("…" if len(orphans) > 10 else ""))
        most_backlinked = sorted(graph.incoming.items(),
                                 key=lambda x: -len(x[1]))[:5]
        for name, backlinks in most_backlinked:
            print(f"被引  {name} ← {len(backlinks)} 篇")
        return 0

    if ns.command == "stats":
        from .index import InvertedIndex

        graph = build_graph(notes)
        idx = InvertedIndex()
        idx.build(notes)
        link_count = sum(len(t) for t in graph.outgoing.values())
        print(f"笔记        {len(notes)}")
        print(f"链接        {link_count}")
        print(f"悬空链接    {len(graph.unresolved)}")
        print(f"孤岛        {len(graph.orphans(list(notes)))}")
        ist = idx.stats()
        print(f"索引词元    {ist['vocabulary']}")
        print(f"索引位置    {ist['postings']}")
        return 0

    print("用法: python -m notesdb {list|query|tags|links|stats}", file=sys.stderr)
    return 2


def _parse(argv: list[str] | None) -> argparse.Namespace:
    parser = build_parser()
    argv = list(sys.argv[1:] if argv is None else argv)
    known = set(parser._subparsers._group_actions[0].choices)  # noqa: SLF001
    if argv and argv[0] in known:
        return parser.parse_args(argv)
    return parser.parse_args(argv)


if __name__ == "__main__":
    sys.exit(main())
