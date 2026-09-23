"""标签体系（M4）：frontmatter.tags 的规范化与过滤。

用户写笔记时 tags 的形态五花八门（列表/逗号串/单值），本模块
负责统一口径：

  note_tags(note) → 排序去重的小写标签列表
    - YAML 列表 ["A", "b"] → ["a", "b"]
    - 逗号串 "a, b, c" → ["a", "b", "c"]
    - 单值 42 → ["42"]（转字符串）
    - 非法类型（映射）→ []（不炸）
  TagIndex：从全库构建 标签 → 笔记集合 的倒排
  filter_by_tags(notes, include, exclude)：
    - include = AND 语义（笔记必须带全部 include 标签）
    - exclude = NOT 语义（带任何一个 exclude 标签即排除）
    - include 为空 = 不过滤

标签的小写化只发生在比较层（返回值保持用户写的大小写会
让去重失败），因此 note_tags 返回小写——标签在笔记工具的
语境里天然大小写不敏感。
"""
from __future__ import annotations

from collections import defaultdict

TAGS_KEY = "tags"


def normalize_tag(tag) -> str | None:
    """单个标签规范化：strip + 小写。非法（空/None）返回 None。"""
    if tag is None:
        return None
    s = str(tag).strip().lower()
    return s or None


def note_tags(note: dict) -> list[str]:
    """笔记的标签列表（排序去重小写）。"""
    fm = note.get("frontmatter") or {}
    raw = fm.get(TAGS_KEY)
    if raw is None:
        return []
    candidates: list = []
    if isinstance(raw, list):
        candidates = raw
    elif isinstance(raw, str):
        # 逗号分隔的字符串形态（手写 YAML 常见）
        candidates = raw.split(",")
    elif isinstance(raw, (int, float, bool)):
        candidates = [raw]
    else:
        return []  # 映射等无法解释的形态
    tags = {t for t in (normalize_tag(c) for c in candidates) if t}
    return sorted(tags)


def build_tag_index(notes: dict[str, dict]) -> dict[str, list[str]]:
    """标签 → 笔记名列表（双双排序）。"""
    by_tag: dict[str, set[str]] = defaultdict(set)
    for name, note in notes.items():
        for tag in note_tags(note):
            by_tag[tag].add(name)
    return {tag: sorted(names) for tag, names in sorted(by_tag.items())}


def filter_by_tags(notes: dict[str, dict],
                   include: list[str] | None = None,
                   exclude: list[str] | None = None) -> dict[str, dict]:
    """按标签过滤笔记（include AND / exclude NOT）。"""
    inc = {normalize_tag(t) for t in (include or []) if normalize_tag(t)}
    exc = {normalize_tag(t) for t in (exclude or []) if normalize_tag(t)}
    out: dict[str, dict] = {}
    for name, note in notes.items():
        tags = set(note_tags(note))
        if inc and not tags >= inc:
            continue
        if exc and tags & exc:
            continue
        out[name] = note
    return out


def tag_summary(notes: dict[str, dict]) -> list[dict]:
    """标签使用统计（按笔记数降序，供报表/标签云）。"""
    idx = build_tag_index(notes)
    items = [{"tag": t, "count": len(names)} for t, names in idx.items()]
    items.sort(key=lambda x: (-x["count"], x["tag"]))
    return items
