"""笔记别名（M26）：frontmatter.aliases 让笔记有多个名字。

Obsidian 风格：`aliases: [别名1, 别名2]`。wikilink 可以用
别名引用——[[别名]] 也解析到本笔记。

  note_aliases(note)          读别名（规范化：strip/去空/去重）
  resolve_name(target, notes) 把 wikilink 目标解析成真实笔记名：
                              先按名字匹配，再按别名匹配；
                              解析不了返回 None（悬空）。
  all_names(notes)            名字 + 别名的完整映射
                              {显示名: 笔记名}（冲突时本名优先）。

链接图（links.build_graph）通过 resolve_name 接入别名——
M26 起悬空判定考虑别名，不再把 [[别名]] 误报为悬空。
"""
from __future__ import annotations

ALIASES_KEY = "aliases"


def note_aliases(note: dict) -> list[str]:
    """笔记的别名列表（保序去重）。非法形态（非列表/非字符串项）忽略。"""
    fm = note.get("frontmatter") or {}
    raw = fm.get(ALIASES_KEY)
    if not isinstance(raw, list):
        return []
    out: list[str] = []
    for item in raw:
        if isinstance(item, str) and item.strip() and item.strip() not in out:
            out.append(item.strip())
    return out


def all_names(notes: dict[str, dict]) -> dict[str, str]:
    """{名字或别名: 笔记名}。本名优先（别名与本名冲突时本名赢）。"""
    mapping: dict[str, str] = {}
    for name in sorted(notes):
        mapping[name] = name  # 本名先占位
    for name in sorted(notes):
        for alias in note_aliases(notes[name]):
            # 别名不覆盖已有映射（本名或更早笔记的本名/别名）
            if alias not in mapping:
                mapping[alias] = name
    return mapping


def resolve_name(target: str, notes: dict[str, dict]) -> str | None:
    """wikilink 目标 → 真实笔记名（本名直通，别名翻译）。"""
    if target in notes:
        return target
    return all_names(notes).get(target)
