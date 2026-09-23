"""笔记编辑操作（M10）：库的写路径。

CLI 的写命令全部走这里（store.store 落盘）：
  new(name, title, tags)     建新笔记（已存在 → 报错不覆盖）
  rename(old, new)           改名 + 全库 wikilink 引用同步更新
  add_tag(name, tag)         frontmatter.tags 追加（幂等）
  remove_tag(name, tag)      tags 移除（没有该标签 → 报错）
  delete(name)               删除笔记（先自动备份——删是危险操作）

rename 的引用同步是本模块的关键约束：改笔记名而不改引用
会造成大批悬空链接，因此 rename 必须原子地完成
「目标笔记改名 + 所有 [[旧名]] 改 [[新名]]」。
"""
from __future__ import annotations

import re

from .model import render_note
from .store import Store

_WIKILINK_RE = re.compile(r"\[\[([^\]\n|]+)(\|[^\]\n]*)?\]\]")


class EditError(ValueError):
    """编辑操作失败（目标不存在/已存在等，消息面向用户）。"""


def new(root, name: str, title: str | None = None,
        tags: list[str] | None = None, body: str = "") -> dict:
    """新建笔记。已存在抛 EditError。"""
    store = Store(root)
    notes, _ = store.load()
    if name in notes:
        raise EditError(f"笔记已存在: {name}")
    fm: dict = {}
    if title:
        fm["title"] = title
    if tags:
        fm["tags"] = tags
    note = {"frontmatter": fm or None, "body": body}
    store.store(name, note)
    return note


def rename(root, old: str, new_name: str) -> int:
    """改名并同步全部引用。返回更新引用的笔记数。

    全部替换先在内存完成、统一落盘：目标笔记存到新名下，
    旧名文件删除，其余引用它的笔记各自写回。中途失败最多
    留下「旧名未删」的中间态，不会丢内容。
    """
    store = Store(root)
    notes, _ = store.load()
    if old not in notes:
        raise EditError(f"笔记不存在: {old}")
    if new_name in notes and new_name != old:
        raise EditError(f"目标名已存在: {new_name}")

    updated = 0
    to_write: list[tuple[str, dict]] = []
    target_note = notes[old]
    for name, note in notes.items():
        body = note.get("body", "")
        new_body, n = _replace_target(body, old, new_name)
        if n:
            note["body"] = new_body
            if name == old:
                target_note = note  # 自引用更新后的目标笔记（写到新名）
            else:
                to_write.append((name, note))
                updated += n

    # 目标笔记本体落到新名（frontmatter.title 不动——那是显示名）
    to_write.append((new_name, target_note))
    for name, note in to_write:
        store.store(name, note)
    if old != new_name:
        _delete_file(store, old)
    return updated


def _replace_target(body: str, old: str, new_name: str) -> tuple[str, int]:
    """把 body 里的 [[old]]/[[old|alias]] 目标换成 new_name。"""
    count = 0

    def sub(m: re.Match) -> str:
        nonlocal count
        if m.group(1).strip() == old:
            count += 1
            alias = m.group(2) or ""
            return f"[[{new_name}{alias}]]"
        return m.group(0)

    return _WIKILINK_RE.sub(sub, body), count


def _delete_file(store: Store, name: str) -> None:
    path = store.notes_dir / f"{name}.md"
    if path.exists():
        path.unlink()


def add_tag(root, name: str, tag: str) -> dict:
    """frontmatter.tags 追加标签（幂等）。"""
    from .tags import note_tags

    store = Store(root)
    notes, _ = store.load()
    if name not in notes:
        raise EditError(f"笔记不存在: {name}")
    note = notes[name]
    current = note_tags(note)
    t = tag.strip().lower()
    if t in current:
        return note  # 幂等：已存在直接成功
    fm = note.get("frontmatter") or {}
    fm["tags"] = sorted([*current, t])
    note["frontmatter"] = fm
    store.store(name, note)
    return note


def remove_tag(root, name: str, tag: str) -> dict:
    from .tags import note_tags

    store = Store(root)
    notes, _ = store.load()
    if name not in notes:
        raise EditError(f"笔记不存在: {name}")
    note = notes[name]
    current = note_tags(note)
    t = tag.strip().lower()
    if t not in current:
        raise EditError(f"笔记 {name} 没有标签 {t}")
    remaining = [x for x in current if x != t]
    fm = note.get("frontmatter") or {}
    if remaining:
        fm["tags"] = remaining
    else:
        fm.pop("tags", None)
    note["frontmatter"] = fm or None
    store.store(name, note)
    return note


def delete(root, name: str, backup_first: bool = True) -> None:
    """删除笔记。默认先做一次全库备份（删是危险操作）。"""
    store = Store(root)
    notes, _ = store.load()
    if name not in notes:
        raise EditError(f"笔记不存在: {name}")
    if backup_first:
        from .backup import backup as do_backup
        do_backup(root)
    _delete_file(store, name)
