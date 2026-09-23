"""CLI 入口：python -m notesdb <命令>。

只读命令：
  list / query / tags / links / stats / export / lint / report
  walk [n]          随机漫游 n 篇（--seed 可复现）
  today             今日每日笔记（不存在则给出创建提示）
  similar <笔记>     相似笔记推荐
  suggest <笔记>     链接建议 + 悬空修复建议

写入命令：
  new <名> [--title] [--tag…]     新建笔记
  rename <旧> <新>                改名（引用同步）
  delete <名>                     删除（先备份）
  tag add/remove <笔记> <标签>    标签增删
  import <目录> [--mode]          批量导入
  backup [--keep n] / restore <zip> / backups
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from . import __version__
from .daily import today_name
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

    # 只读
    sub.add_parser("list", help="列出全部笔记")
    p_query = sub.add_parser("query", help="执行查询")
    p_query.add_argument("query_string", help="查询串（见 query 模块语法）")
    sub.add_parser("tags", help="标签使用统计")
    sub.add_parser("links", help="链接图摘要")
    sub.add_parser("stats", help="库统计")
    sub.add_parser("export", help="静态站点导出")
    sub.add_parser("lint", help="库健康检查")
    sub.add_parser("report", help="统计报表（Markdown）")

    p_walk = sub.add_parser("walk", help="随机漫游笔记")
    p_walk.add_argument("steps", nargs="?", type=int, default=5)
    p_walk.add_argument("--seed", type=int, default=None)

    sub.add_parser("today", help="今日每日笔记状态")
    p_sim = sub.add_parser("similar", help="相似笔记推荐")
    p_sim.add_argument("name")
    p_sug = sub.add_parser("suggest", help="链接建议")
    p_sug.add_argument("name")

    # 写入
    p_new = sub.add_parser("new", help="新建笔记")
    p_new.add_argument("name")
    p_new.add_argument("--title")
    p_new.add_argument("--tag", action="append", default=[])
    p_ren = sub.add_parser("rename", help="改名（引用同步）")
    p_ren.add_argument("old")
    p_ren.add_argument("new")
    p_del = sub.add_parser("delete", help="删除笔记（先备份）")
    p_del.add_argument("name")
    p_tag = sub.add_parser("tag", help="标签增删")
    p_tag.add_argument("op", choices=["add", "remove"])
    p_tag.add_argument("name")
    p_tag.add_argument("tag")
    p_imp = sub.add_parser("import", help="批量导入目录")
    p_imp.add_argument("src")
    p_imp.add_argument("--mode", choices=["skip", "suffix", "overwrite"],
                       default="skip")

    p_bk = sub.add_parser("backup", help="全库备份")
    p_bk.add_argument("--keep", type=int, default=10)
    sub.add_parser("backups", help="列出备份")
    p_rs = sub.add_parser("restore", help="从备份恢复")
    p_rs.add_argument("zip_path")
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

    # 写入命令各自加载（要拿最新状态）
    if ns.command in ("new", "rename", "delete", "tag", "import",
                      "backup", "restore", "backups"):
        return _write_commands(ns)

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
        from .snippet import snippets_for

        hits = run(notes, q)
        print(f"命中 {len(hits)}/{len(notes)}")
        idx = None
        if q.words or q.phrases:
            from .index import InvertedIndex
            idx = InvertedIndex()
            idx.build(notes)
        for name in sorted(hits):
            print(f"  {name}")
            if idx:
                lines = idx.search(" ".join(q.words + q.phrases)).get(name, [])
                for s in snippets_for(hits[name].get("body", ""), lines):
                    print(f"    {' | '.join(s.splitlines())}")
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
        for name, backlinks in sorted(graph.incoming.items(),
                                      key=lambda x: -len(x[1]))[:5]:
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

    if ns.command == "export":
        from .exporter import export_site

        out = export_site(ns.root, notes)
        print(f"已导出 {len(notes)} 篇 → {out}")
        return 0

    if ns.command == "lint":
        from .lint import check_library, has_errors

        issues = check_library(notes)
        for i in issues:
            print(f"  {i}")
        if not issues:
            print("✅ 库健康，无问题")
        return 1 if has_errors(issues) else 0

    if ns.command == "report":
        from .report import build_report, render_report

        print(render_report(build_report(notes)))
        return 0

    if ns.command == "walk":
        from .walk import walk

        graph = build_graph(notes)
        for name in walk(graph, notes, steps=ns.steps, seed=ns.seed):
            print(f"  {name}")
        return 0

    if ns.command == "today":
        name = today_name()
        if name in notes:
            print(f"今日笔记已存在: {name}")
        else:
            print(f"今日笔记尚未创建: {name}")
            print(f"  python -m notesdb new {name}")
        return 0

    if ns.command == "similar":
        from .similar import similar_to

        try:
            for other, sim in similar_to(ns.name, notes):
                print(f"  {other}  (相似度 {sim})")
        except ValueError as e:
            print(str(e), file=sys.stderr)
            return 2
        return 0

    if ns.command == "suggest":
        from .suggest import suggest_backlink_targets, suggest_links

        try:
            links = suggest_links(ns.name, notes)
            fixes = suggest_backlink_targets(ns.name, notes)
        except ValueError as e:
            print(str(e), file=sys.stderr)
            return 2
        if links:
            print("可考虑链接（内容相关但尚未连接）:")
            for other, sim in links:
                print(f"  [[{other}]]  (相似度 {sim})")
        if fixes:
            print("悬空链接修复建议:")
            for f in fixes:
                if f["best"]:
                    print(f"  [[{f['dangling']}]] → [[{f['best']['name']}]]"
                          f"（编辑距离 {f['best']['distance']}）")
                else:
                    print(f"  [[{f['dangling']}]] 库里无相近名，建议新建")
        if not links and not fixes:
            print("暂无建议")
        return 0

    print("用法见 python -m notesdb --help", file=sys.stderr)
    return 2


def _write_commands(ns) -> int:
    """写入命令（独立处理：各自加载最新状态）。"""
    if ns.command == "new":
        from .edit import EditError, new
        try:
            new(ns.root, ns.name, title=ns.title, tags=ns.tag or None)
            print(f"已创建: {ns.name}")
            print(f"  {os.path.join(ns.root, 'notes', ns.name + '.md')}")
            return 0
        except (EditError, ValueError) as e:
            print(str(e), file=sys.stderr)
            return 2

    if ns.command == "rename":
        from .edit import EditError, rename
        try:
            updated = rename(ns.root, ns.old, ns.new)
            print(f"已改名: {ns.old} → {ns.new}（同步更新 {updated} 处引用）")
            return 0
        except (EditError, ValueError) as e:
            print(str(e), file=sys.stderr)
            return 2

    if ns.command == "delete":
        from .edit import EditError, delete
        try:
            delete(ns.root, ns.name)
            print(f"已删除: {ns.name}（删除前已自动备份）")
            return 0
        except (EditError, ValueError) as e:
            print(str(e), file=sys.stderr)
            return 2

    if ns.command == "tag":
        from .edit import EditError, add_tag, remove_tag
        try:
            if ns.op == "add":
                add_tag(ns.root, ns.name, ns.tag)
                print(f"已添加标签: {ns.tag}")
            else:
                remove_tag(ns.root, ns.name, ns.tag)
                print(f"已移除标签: {ns.tag}")
            return 0
        except (EditError, ValueError) as e:
            print(str(e), file=sys.stderr)
            return 2

    if ns.command == "import":
        from .importer import import_dir
        try:
            r = import_dir(ns.src, ns.root, mode=ns.mode)
        except (FileNotFoundError, ValueError) as e:
            print(str(e), file=sys.stderr)
            return 2
        print(r.summary())
        for old, new in r.renamed:
            print(f"  重命名: {old} → {new}")
        for s in r.skipped:
            print(f"  跳过: {s}")
        for e in r.errors:
            print(f"  失败: {e}")
        return 0

    if ns.command == "backup":
        from .backup import backup
        path = backup(ns.root, keep=ns.keep)
        print(f"已备份 → {path}")
        return 0

    if ns.command == "backups":
        from .backup import list_backups
        for p in list_backups(ns.root):
            print(f"  {p.name}")
        return 0

    if ns.command == "restore":
        from .backup import BACKUP_DIRNAME, restore

        # 接受完整路径或备份名（backups 命令输出的名字直接可用）
        target = Path(ns.zip_path)
        if not target.exists():
            candidate = Path(ns.root) / BACKUP_DIRNAME / ns.zip_path
            if candidate.exists():
                target = candidate
        try:
            count = restore(ns.root, target)
            print(f"已恢复 {count} 篇笔记")
            return 0
        except (FileNotFoundError, ValueError) as e:
            print(str(e), file=sys.stderr)
            return 2

    return 2


def _parse(argv: list[str] | None) -> argparse.Namespace:
    parser = build_parser()
    argv = list(sys.argv[1:] if argv is None else argv)
    known = set(parser._subparsers._group_actions[0].choices)
    if argv and argv[0] in known:
        return parser.parse_args(argv)
    return parser.parse_args(argv)


if __name__ == "__main__":
    sys.exit(main())
