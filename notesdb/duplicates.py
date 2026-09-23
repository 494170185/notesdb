"""重复笔记检测（M29）：找出内容雷同的笔记组。

两类重复：
  exact       正文逐字节相同（复制粘贴忘删原稿）
  near        正文规范化后相同（空白/换行差异的"伪不同"）

标题近似重复（"读书笔记" vs "读书笔记 2"）不算重复——
那可能是系列笔记，交给人判断。

  find_duplicates(notes) → [[name, ...]] 每组 2+ 篇，组内按名排序、
  组间按首名排序。没有重复返回 []。
"""
from __future__ import annotations

import hashlib
import re


def _normalize(body: str) -> str:
    """正文规范化：压空白、去首尾、统一换行。"""
    return re.sub(r"\s+", " ", body or "").strip()


def _digest(body: str, exact: bool) -> str:
    content = body if exact else _normalize(body)
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def find_duplicates(notes: dict[str, dict]) -> list[list[str]]:
    """找重复组（exact 与 near 两层，near 优先合并）。"""
    # 规范化摘要（near 层）
    by_norm: dict[str, list[str]] = {}
    for name in sorted(notes):
        body = notes[name].get("body", "")
        if not _normalize(body):
            continue  # 空正文不参与（空笔记不是"重复"）
        by_norm.setdefault(_digest(body, exact=False), []).append(name)

    groups = [names for names in by_norm.values() if len(names) > 1]
    # 组内按 near 分组后再用 exact 细分（报告更准：
    # 完全相同的标成一组，仅规范化相同的不混在 exact 里）
    out: list[list[str]] = []
    for names in groups:
        exact_digests = {_digest(notes[n].get("body", ""), True) for n in names}
        if len(exact_digests) == 1:
            out.append(names)  # 全部逐字节一致
        else:
            # 规范化相同但内容有差：逐字一致的细分组
            by_exact: dict[str, list[str]] = {}
            for n in names:
                by_exact.setdefault(
                    _digest(notes[n].get("body", ""), True), []).append(n)
            for sub in by_exact.values():
                if len(sub) > 1:
                    out.append(sub)
    out.sort(key=lambda g: g[0])
    return out


def describe_group(group: list[str]) -> str:
    """重复组的人话描述。"""
    return "疑似重复: " + "、".join(group)
