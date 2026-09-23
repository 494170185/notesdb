"""TODO 提取（M21）：从笔记正文挖任务项。

口径（Markdown 事实约定）：
  - [ ] 任务        未完成
  - [x] 任务        已完成
  - - TODO: 任务    文字型 todo（TODO:/FIXME:/XXX: 三种前缀）

提取后聚合：
  pending(notes)      全库未完成任务（含出处笔记与行号）
  by_note(notes)      每篇笔记各自的任务列表
  progress(notes)     完成率（有 checkbox 的笔记）

用途：CLI 的 todo 命令、导出页的任务汇总区。
"""
from __future__ import annotations

import re

_CHECKBOX_RE = re.compile(r"^\s*[-*+]\s+\[([ xX])\]\s+(.*)$")
_TODO_RE = re.compile(r"^\s*[-*+]\s+(TODO|FIXME|XXX):\s*(.*)", re.IGNORECASE)


def extract_todos(note: dict) -> list[dict]:
    """单篇笔记的任务项。返回 [{done, text, line}]（行号 0 起）。"""
    out: list[dict] = []
    for line_no, line in enumerate((note.get("body") or "").splitlines()):
        m = _CHECKBOX_RE.match(line)
        if m:
            out.append({"done": m.group(1).lower() == "x",
                        "text": m.group(2).strip(), "line": line_no})
            continue
        m = _TODO_RE.match(line)
        if m:
            out.append({"done": False, "text": m.group(2).strip(),
                        "line": line_no, "kind": m.group(1).upper()})
    return out


def by_note(notes: dict[str, dict]) -> dict[str, list[dict]]:
    """每篇笔记的任务（只含有任务的笔记）。"""
    out = {}
    for name, note in sorted(notes.items()):
        todos = extract_todos(note)
        if todos:
            out[name] = todos
    return out


def pending(notes: dict[str, dict]) -> list[tuple[str, dict]]:
    """全库未完成任务 [(note_name, todo)]（笔记名升序、行序）。"""
    out: list[tuple[str, dict]] = []
    for name, todos in sorted(by_note(notes).items()):
        for todo in todos:
            if not todo["done"]:
                out.append((name, todo))
    return out


def progress(notes: dict[str, dict]) -> dict:
    """checkbox 完成率（只统计有 checkbox 的笔记）。

    文字型 TODO 不计入（没有"完成"形态）。
    """
    total = done = 0
    for todos in by_note(notes).values():
        for t in todos:
            if "kind" in t:  # 文字型跳过
                continue
            total += 1
            if t["done"]:
                done += 1
    return {"total": total, "done": done,
            "ratio": round(done / total, 3) if total else None}
