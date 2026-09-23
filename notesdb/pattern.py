"""笔记名模式匹配（M33）：glob 与正则两种名字选择器。

exclude 配置用 glob；高级查询需要正则。统一收口：

  match_glob(name, pattern)     fnmatch 大小写不敏感（Windows 习惯）
  match_regex(name, pattern)    正则（re.search 语义，坏模式抛 ValueError）
  match_any(name, patterns, mode)  多模式任一命中
  select(notes, patterns, mode)    按名字模式筛笔记 {name: note}

mode: "glob" | "regex"。非法正则在解析期报错（不是静默空结果）。
"""
from __future__ import annotations

import fnmatch
import re

MODES = ("glob", "regex")


def match_glob(name: str, pattern: str) -> bool:
    """glob 匹配（大小写不敏感——Windows 文件名语义）。"""
    return fnmatch.fnmatch(name, pattern)


def match_regex(name: str, pattern: str) -> bool:
    """正则匹配（search 语义）。坏模式抛 ValueError。"""
    try:
        return re.search(pattern, name) is not None
    except re.error as e:
        raise ValueError(f"正则模式不合法: {pattern!r} ({e})") from None


def compile_patterns(patterns: list[str], mode: str = "glob") -> list:
    """预编译模式列表（glob→fnmatch 转正则；regex→re.compile）。

  返回 matcher 列表，match_any 用；解析错误在此抛出
    （早失败，别等逐笔记时才炸）。
    """
    if mode not in MODES:
        raise ValueError(f"mode 只支持 {MODES}，收到 {mode!r}")
    compiled = []
    for p in patterns:
        if not p:
            continue
        if mode == "glob":
            compiled.append(re.compile(fnmatch.translate(p), re.IGNORECASE))
        else:
            try:
                compiled.append(re.compile(p))
            except re.error as e:
                raise ValueError(f"正则模式不合法: {p!r} ({e})") from None
    return compiled


def match_any(name: str, patterns: list[str], mode: str = "glob") -> bool:
    """任一模式命中即 True（便捷入口，热路径用 compile_patterns）。"""
    if mode not in MODES:
        raise ValueError(f"mode 只支持 {MODES}，收到 {mode!r}")
    if mode == "glob":
        return any(match_glob(name, p) for p in patterns if p)
    return any(match_regex(name, p) for p in patterns if p)


def select(notes: dict[str, dict], patterns: list[str],
           mode: str = "glob") -> dict[str, dict]:
    """按名字模式筛笔记。"""
    if not patterns:
        return dict(notes)
    compiled = compile_patterns(patterns, mode)
    return {name: note for name, note in notes.items()
            if any(c.search(name) for c in compiled)}
