"""快速捕获（M35）：把一句话闪念直接存成 inbox 笔记。

用法：闪念来了不想开编辑器——
  python -m notesdb inbox "想到一个点子"

落点：notes/inbox.md（单文件追加式，每条带时间戳一节）。
定期把 inbox 里的条目整理成正式笔记（人工消化，工具不越俎代庖）。

  append(root, text)      追加一条（建文件/追加节）
  read(root)              读全部条目 [{time, text}]
  clear(root)             清空（整理完归档）

inbox.md 本身就是普通笔记（可查询/导出），不引入特殊存储。
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

INBOX_NAME = "inbox"

_ENTRY_TMPL = "## {time}\n\n{text}\n\n"


def _inbox_path(root) -> Path:
    from .store import Store

    return Store(root).path_of(INBOX_NAME)


def append(root, text: str) -> str:
    """追加一条闪念。返回 inbox 笔记名。"""
    text = (text or "").strip()
    if not text:
        raise ValueError("闪念内容不能为空")
    path = _inbox_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    entry = _ENTRY_TMPL.format(
        time=datetime.now().strftime("%Y-%m-%d %H:%M"), text=text)
    if path.exists():
        with open(path, "a", encoding="utf-8", newline="\n") as f:
            f.write(entry)
    else:
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write("---\ntitle: 收件箱\ntags: [inbox]\n---\n" + entry)
    return INBOX_NAME


def read(root) -> list[dict]:
    """读全部条目 [{time, text}]（时间升序）。"""
    path = _inbox_path(root)
    if not path.exists():
        return []
    content = path.read_text(encoding="utf-8")
    from .model import parse_note

    body = parse_note(content)["body"]
    entries: list[dict] = []
    for section in body.split("## ")[1:]:
        lines = section.strip().splitlines()
        if not lines:
            continue
        entries.append({
            "time": lines[0].strip(),
            "text": "\n".join(lines[1:]).strip(),
        })
    return entries


def clear(root) -> int:
    """清空收件箱。返回清掉的条目数。"""
    entries = read(root)
    if not entries:
        return 0
    path = _inbox_path(root)
    if path.exists():
        path.unlink()
    return len(entries)
