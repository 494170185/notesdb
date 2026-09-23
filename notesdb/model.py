"""笔记模型（M1）：一篇笔记 = 一个 Markdown 文件 + frontmatter。

项目要处理的最小数据单元。设计要点：

- frontmatter 是 YAML 块（`---` 围起来），字段自由；本模块只
  负责把「正文文本」拆成「frontmatter dict + 正文 str」，
  不解释字段含义（字段语义由索引/查询层定义）；
- 解析失败（YAML 坏、块残缺）不抛异常：返回 (None, 原文)——
  坏 frontmatter 的笔记照样入库（正文检索不受影响），
  错误原因放在 parse_error 字段里让调用方决定要不要报；
- 笔记名即文件名（不带 .md 扩展名）。这是全项目的唯一 ID，
  wikilink 引用它，索引用它做主键。
"""
from __future__ import annotations

import re

import yaml

_FM_RE = re.compile(
    r"\A---[ \t]*\r?\n(?:(.*?)\r?\n)?---[ \t]*\r?\n?(.*)\Z", re.DOTALL)


def split_frontmatter(text: str) -> tuple[dict | None, str]:
    """把笔记文本拆成 (frontmatter, body)。

    无 frontmatter → (None, 原文)。
    frontmatter 块存在但 YAML 解析失败 → (None, 原文)：宁可没有
    元数据也不要把整篇笔记拒之门外。
    """
    if text is None:
        return None, ""
    m = _FM_RE.match(text.lstrip("\ufeff"))
    if not m:
        return None, text
    raw_fm, body = m.group(1), m.group(2)
    if raw_fm is None or raw_fm.strip() == "":
        # `---\n---\n` 空块：合法但无字段
        return {}, body
    try:
        fm = yaml.safe_load(raw_fm)
    except yaml.YAMLError:
        return None, text
    if fm is None:
        # 显式 null（`---\n~\n---`）按空处理
        return {}, body
    if not isinstance(fm, dict):
        # frontmatter 必须是映射；标量/列表是写错了格式
        return None, text
    return fm, body


def parse_note(text: str) -> dict:
    """解析成统一笔记 dict（name 由调用方补）。

    返回结构：
      frontmatter: dict | None（None = 无/坏 frontmatter）
      frontmatter_error: bool（True = 有块但坏了）
      body: str（正文，不含 frontmatter 块）
    """
    fm, body = split_frontmatter(text)
    had_block = _FM_RE.match((text or "").lstrip("\ufeff")) is not None
    return {
        "frontmatter": fm,
        "frontmatter_error": had_block and fm is None,
        "body": body,
    }


def render_note(frontmatter: dict | None, body: str) -> str:
    """frontmatter + 正文 → 笔记文本（写出用，与解析对称）。

    frontmatter 为 None/空 dict 时只写正文（保持「无元数据笔记」
    的往返一致：解析不到就不写出空块）。
    """
    if not frontmatter:
        return body
    fm_text = yaml.safe_dump(frontmatter, allow_unicode=True,
                             sort_keys=False, default_flow_style=False)
    return f"---\n{fm_text}---\n{body}"


TITLE_KEY = "title"


def note_title(note: dict) -> str | None:
    """标题取 frontmatter.title；没有返回 None（调用方回退用笔记名）。"""
    fm = note.get("frontmatter") or {}
    t = fm.get(TITLE_KEY)
    return t if isinstance(t, str) and t.strip() else None
