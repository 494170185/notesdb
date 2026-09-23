"""链接图导出（M30）：把笔记链接图转成 Graphviz DOT。

可视化是笔记库审计的捷径：一眼看到孤岛、断链区域、
枢纽的辐射形态。Graphviz 是通用渲染目标（dot/neato/在线
编辑器都吃 DOT）。

  to_dot(notes, graph)     DOT 文本（UTF-8 安全、节点按存在性着色）
  write_dot(root, notes)   落盘 output/graph.dot 并返回路径

设计：
- 存在的笔记 = 实线边框节点；悬空目标 = 红色虚线节点；
- 孤岛（无边）也输出（isolated 节点，形状区分）；
- 名字里的引号/反斜杠转义（DOT 语法安全）。
"""
from __future__ import annotations

import os
from pathlib import Path

from .links import LinkGraph, build_graph

DOT_DIRNAME = "output"


def to_dot(notes: dict[str, dict], graph: LinkGraph | None = None) -> str:
    """渲染 DOT 文本。"""
    graph = graph or build_graph(notes)
    existing = set(notes)
    lines = ["digraph notesdb {", "  rankdir=LR;", "  node [fontname=\"Microsoft YaHei\"];"]

    linked = {n for n in notes
              if graph.outgoing.get(n) or graph.incoming.get(n)}
    for name in sorted(notes):
        if name in linked:
            lines.append(f'  {_q(name)} [label={_q(name)}];')
        else:
            lines.append(f'  {_q(name)} [label={_q(name)}, shape=box, style=dotted];')

    for target in graph.unresolved:
        lines.append(f'  {_q(target)} [label={_q(target)}, color=red, style=dashed];')

    for name in sorted(notes):
        for target in graph.outgoing.get(name, []):
            if target in existing:
                lines.append(f"  {_q(name)} -> {_q(target)};")
            else:
                lines.append(f"  {_q(name)} -> {_q(target)} [color=red, style=dashed];")

    lines.append("}")
    return "\n".join(lines) + "\n"


def write_dot(root: str | os.PathLike, notes: dict[str, dict],
              graph: LinkGraph | None = None) -> Path:
    """落盘 graph.dot。返回文件路径。"""
    out_dir = Path(root) / DOT_DIRNAME
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "graph.dot"
    path.write_text(to_dot(notes, graph), encoding="utf-8")
    return path


def _q(name: str) -> str:
    """DOT 标识符：始终加引号 + 转义内部引号与反斜杠。"""
    escaped = name.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'
