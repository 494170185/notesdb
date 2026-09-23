"""库统计报表（M12）：把全库画像汇总成机器/人类两种格式。

JSON 报表（build_report）字段：
  notes            笔记总数
  words            正文总词数（tokenize 词元口径）
  links / dangling / orphans   链接图三指标
  top_tags         标签使用 Top N
  top_linked       被引用最多 Top N（库的知识枢纽）
  daily_coverage   每日笔记覆盖天数
  index            倒排索引规模

Markdown 报表（render_report）：同一数据的 CLI/导出可读版。
报表是只读快照——写盘由调用方决定（CLI、导出器各自接）。
"""
from __future__ import annotations

from .daily import is_daily
from .index import InvertedIndex
from .links import build_graph
from .tags import tag_summary
from .tokenize import tokenize

TOP_N = 10


def build_report(notes: dict[str, dict]) -> dict:
    """全库统计（数据源：链接图 + 标签 + 索引 + 词元）。"""
    graph = build_graph(notes)
    idx = InvertedIndex()
    idx.build(notes)

    words = 0
    for note in notes.values():
        words += len(tokenize(note.get("body", "")))

    top_tags = tag_summary(notes)[:TOP_N]
    top_linked = sorted(
        ((name, len(graph.backlinks(name))) for name in notes),
        key=lambda x: (-x[1], x[0]))[:TOP_N]
    daily_count = sum(1 for name in notes if is_daily(name))

    link_total = sum(len(t) for t in graph.outgoing.values())
    return {
        "notes": len(notes),
        "words": words,
        "links": link_total,
        "dangling": len(graph.unresolved),
        "orphans": len(graph.orphans(list(notes))),
        "top_tags": top_tags,
        "top_linked": [{"name": n, "backlinks": c} for n, c in top_linked],
        "daily_notes": daily_count,
        "index_vocabulary": idx.stats()["vocabulary"],
        "index_postings": idx.stats()["postings"],
    }


def render_report(report: dict) -> str:
    """Markdown 版报表（人类可读）。"""
    lines = [
        "# 库统计报表",
        "",
        f"- 笔记：**{report['notes']}** 篇（每日笔记 {report['daily_notes']}）",
        f"- 词元：{report['words']:,}",
        f"- 链接：{report['links']}（悬空 {report['dangling']}，孤岛 {report['orphans']}）",
        f"- 索引：词元 {report['index_vocabulary']:,} / 位置 {report['index_postings']:,}",
        "",
        "## 高频标签",
        "",
    ]
    if report["top_tags"]:
        for item in report["top_tags"]:
            bar = "█" * min(item["count"], 20)
            lines.append(f"- `{item['tag']}` ×{item['count']} {bar}")
    else:
        lines.append("- （无标签）")

    lines += ["", "## 知识枢纽（被引 Top）", ""]
    if report["top_linked"]:
        for item in report["top_linked"]:
            if item["backlinks"] > 0:
                lines.append(f"- [[{item['name']}]] ← {item['backlinks']} 篇引用")
    if not any(i["backlinks"] > 0 for i in report["top_linked"]):
        lines.append("- （还没有链接关系）")
    return "\n".join(lines) + "\n"
