"""外部引用检查（M27）：笔记里引用的本地文件是否存在。

Markdown 引用非 wikilink 的本地资源：
  ![alt](path)   图片
  [text](path)   链接（相对路径且非 http/锚点）

断链的本地引用（文件被移走/改名）在浏览导出页时才发现
就晚了。本模块扫描全部本地引用并核对磁盘：

  extract_refs(body)          本地引用（path, 行号）
  check_refs(notes, root)     全库检查 → [{note, path, line, exists}]

口径：只查**相对路径**（http(s)/mailto/#锚点跳过）；
路径基于库根（笔记可能嵌在子目录，引用从笔记所在目录
解析——与 Markdown 渲染器的语义一致）。
"""
from __future__ import annotations

import os
import re
from pathlib import Path

_MD_REF_RE = re.compile(r"!?\[([^\]]*)\]\(([^)]+)\)")
_SKIP_PREFIXES = ("http://", "https://", "mailto:", "#", "data:")


def extract_refs(body: str) -> list[tuple[str, int]]:
    """正文里的本地文件引用 [(path, line_no)]。

  `![img](pic.png)` 与 `[doc](../docs/a.pdf)` 都算；
    URL 片段（#frag）剥掉再判。
    """
    out: list[tuple[str, int]] = []
    for line_no, line in enumerate((body or "").splitlines()):
        for m in _MD_REF_RE.finditer(line):
            raw = m.group(2).strip()
            # 剥 URL 片段与查询（pic.png#x / pic.png?v=2）
            for sep in ("#", "?"):
                raw = raw.split(sep, 1)[0]
            if not raw or raw.lower().startswith(_SKIP_PREFIXES):
                continue
            # Windows 绝对路径与盘符跳过（不可移植，不算库内引用）
            if re.match(r"^[a-zA-Z]:[/\\]", raw) or raw.startswith(("\\\\", "/")):
                continue
            out.append((raw, line_no))
    return out


def check_refs(notes: dict[str, dict], root: str | os.PathLike) -> list[dict]:
    """全库本地引用核对。返回问题列表（只含不存在的）。"""
    root = Path(root)
    problems: list[dict] = []
    for name in sorted(notes):
        note = notes[name]
        base = (root / "notes" / name).parent  # 引用相对笔记所在目录
        for path, line in extract_refs(note.get("body", "")):
            target = (base / path.replace("\\", "/")).resolve()
            if not target.exists():
                problems.append({"note": name, "path": path, "line": line})
    return problems


def describe_problem(p: dict) -> str:
    """问题的人话描述（CLI/lint 输出）。"""
    return f"{p['note']} 引用的文件不存在: {p['path']}（第 {p['line'] + 1} 行）"
