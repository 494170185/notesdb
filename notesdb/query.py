"""查询语言（M5）：把一个查询字符串编译成对笔记库的结构化检索。

语法（子集，靠空格与关键字切分，不引外部解析库）：

    词             全文检索（多词 AND）
    tag:work       标签过滤（可多个，AND）
    -tag:home      排除标签
    "精确短语"      短语检索（保序）
    link:目标      引用了某笔记（backlink 查询的出链侧）
    orphan         只看孤岛笔记
    unresolved     只看带悬空链接的笔记

示例：
    python -m notesdb query 'tag:work "季度复盘" -tag:archive'

解析成 Query 对象（数据类），执行由 query.run 负责（组合
index/tags/links 三个模块的能力）。解析失败抛 QueryError，
带用户可读的位置信息。
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field


class QueryError(ValueError):
    """查询语法错误（用户输入问题，消息要可读）。"""


@dataclass
class Query:
    """编译后的查询：各条件 AND 组合。"""

    words: list[str] = field(default_factory=list)        # 全文词（AND）
    phrases: list[str] = field(default_factory=list)      # 精确短语
    include_tags: list[str] = field(default_factory=list)
    exclude_tags: list[str] = field(default_factory=list)
    links_to: list[str] = field(default_factory=list)     # 引用了这些笔记
    orphan_only: bool = False
    unresolved_only: bool = False

    def is_empty(self) -> bool:
        return not (self.words or self.phrases or self.include_tags
                    or self.exclude_tags or self.links_to
                    or self.orphan_only or self.unresolved_only)


# "带引号短语" 或 裸词
_TOKEN_RE = re.compile(r'"([^"]*)"|(\S+)')


def parse_query(text: str) -> Query:
    """解析查询字符串。语法错误抛 QueryError。"""
    q = Query()
    if text is None:
        return q
    for m in _TOKEN_RE.finditer(text):
        phrase, bare = m.group(1), m.group(2)
        if phrase is not None:
            if phrase.strip():
                q.phrases.append(phrase.strip())
            continue
        token = bare
        if token == "orphan":
            q.orphan_only = True
        elif token == "unresolved":
            q.unresolved_only = True
        elif token.startswith("tag:"):
            tag = token[len("tag:"):].strip().lower()
            if not tag:
                raise QueryError(f"tag: 后面要有标签名（位置 {m.start()}）")
            q.include_tags.append(tag)
        elif token.startswith("-tag:"):
            tag = token[len("-tag:"):].strip().lower()
            if not tag:
                raise QueryError(f"-tag: 后面要有标签名（位置 {m.start()}）")
            q.exclude_tags.append(tag)
        elif token.startswith("link:"):
            target = token[len("link:"):].strip()
            if not target:
                raise QueryError(f"link: 后面要有笔记名（位置 {m.start()}）")
            q.links_to.append(target)
        else:
            q.words.append(token)
    return q


def describe(q: Query) -> str:
    """人话描述查询（CLI 回显用）。"""
    parts: list[str] = []
    if q.words:
        parts.append("全文: " + " AND ".join(q.words))
    for p in q.phrases:
        parts.append(f'短语: "{p}"')
    if q.include_tags:
        parts.append("标签: " + " + ".join(q.include_tags))
    if q.exclude_tags:
        parts.append("排除标签: " + " / ".join(q.exclude_tags))
    if q.links_to:
        parts.append("链接到: " + " / ".join(q.links_to))
    if q.orphan_only:
        parts.append("仅孤岛")
    if q.unresolved_only:
        parts.append("仅带悬空链接")
    return "；".join(parts) if parts else "（空查询=全部笔记）"
