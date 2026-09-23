"""Wikilink 提取与链接图（M2）。

`[[笔记名]]` 与 `[[笔记名|显示文字]]` 是 Markdown 的事实扩展
（Obsidian 风格）。本模块负责：

1. extract_wikilinks(body)：正文中全部 wikilink 引用（保持出现顺序）；
2. extract_wikilinks_ignoring_code(body)：代码块/行内代码里的
   `[[x]]` 不算链接（示例文档不产生虚假引用）；
3. LinkGraph：由 {name: note} 构建有向链接图——
     outgoing[name]  = 该笔记引用了谁（去重）
     incoming[name]  = 谁引用了该笔记（backlink，去重）
     unresolved      = 引用了但库里不存在的名字（悬空链接）

悬空链接是特性不是错误：写笔记时先埋 `[[未来要写的]]` 是常见
工作流，图谱必须把它显示出来（红色节点），而不是吞掉。
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

# `[[名字]]` 或 `[[名字|显示]]`；名字内不允许 ] 与换行
_WIKILINK_RE = re.compile(r"\[\[([^\]\n|]+)(?:\|[^\]\n]*)?\]\]")

# 行内代码（`…`）——围栏检测在行状态机里做，不需要单独正则
_INLINE_CODE_RE = re.compile(r"`[^`\n]*`")


def extract_wikilinks(body: str) -> list[str]:
    """提取正文中全部 wikilink 目标名（按出现顺序，含重复）。"""
    if not body:
        return []
    return [m.group(1).strip() for m in _WIKILINK_RE.finditer(body)
            if m.group(1).strip()]


def extract_wikilinks_ignoring_code(body: str) -> list[str]:
    """同上，但跳过代码块与行内代码里的链接。

    实现走行状态机：围栏行（```/~~~ 开头）翻转 in_code 状态，
    代码行整行跳过；文本行里的行内代码 `…` 挖掉后再提链接。
    """
    if not body:
        return []
    out: list[str] = []
    in_code = False
    for line in body.splitlines():
        stripped = line.lstrip()
        if stripped.startswith(("```", "~~~")):
            in_code = not in_code
            continue
        if in_code:
            continue
        line = _INLINE_CODE_RE.sub(" ", line)
        out.extend(extract_wikilinks(line))
    return out


@dataclass
class LinkGraph:
    """全库有向链接图。"""

    outgoing: dict[str, list[str]] = field(default_factory=dict)
    incoming: dict[str, list[str]] = field(default_factory=dict)
    unresolved: list[str] = field(default_factory=list)

    def backlinks(self, name: str) -> list[str]:
        """引用了 name 的笔记列表（即 name 的反向链接）。"""
        return self.incoming.get(name, [])

    def orphans(self, names: list[str]) -> list[str]:
        """既没有出链也没有入链的笔记（孤岛节点）。

        outgoing 对库里每个笔记都有条目（哪怕空列表），所以
        判断依据是"有没有实际边"，不是"在不在字典里"。
        """
        has_out = {n for n, targets in self.outgoing.items() if targets}
        has_in = set(self.incoming)
        connected = has_out | has_in
        return [n for n in names if n not in connected]


def build_graph(notes: dict[str, dict]) -> LinkGraph:
    """从 {name: note} 构建链接图。代码块里的链接不计。

    outgoing 含全部链接目标（含悬空目标——图谱要显示你写过它），
    目标是否存在只影响它进不进 incoming。
    """
    g = LinkGraph()
    all_targets: dict[str, set[str]] = {}
    unresolved_set: set[str] = set()

    for name, note in notes.items():
        links = extract_wikilinks_ignoring_code(note.get("body", ""))
        targets: set[str] = set(links)
        unresolved_set.update(t for t in targets if t not in notes)
        all_targets[name] = targets

    for name in notes:
        g.outgoing[name] = sorted(all_targets[name])
    for name, targets in all_targets.items():
        for t in targets:
            if t in notes:
                g.incoming.setdefault(t, []).append(name)
    for name in g.incoming:
        g.incoming[name].sort()

    g.unresolved = sorted(unresolved_set)
    return g
