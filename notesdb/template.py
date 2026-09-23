"""frontmatter 模板变量（M7）：笔记内占位符在导出时替换。

用户场景：反复出现的结构（周报、会议纪要）希望用模板笔记
生成——frontmatter 写变量，正文里 `{{name}}` 引用。

口径（刻意收窄，模板语言一胖就失控）：
  {{key}}          替换为 frontmatter[key] 的字符串形式；
                   缺 key → 保留原文（导出页面看得见没填的占位符，
                   比"整段消失"或"抛错"都友好）
  {{name}}         内置：笔记名（无需写在 frontmatter）
  {{today}}        内置：导出当日（YYYY-MM-DD，渲染时求值）
  {{now}}          内置：导出时刻（HH:MM）
  {{# 评论 }}      模板注释：渲染时整段移除

不做：循环、条件、嵌套引用——那不是笔记场景，是 Jekyll 场景。

渲染入口 render_template(text, front, name)；
导出器渲染正文前先过这一层（render.py 保持纯 Markdown 职责）。
"""
from __future__ import annotations

import datetime as _dt
import re

_PLACEHOLDER_RE = re.compile(r"\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}")
_COMMENT_RE = re.compile(r"\{\{\s*#.*?\}\}", re.DOTALL)

_BUILTIN_RESOLVERS = {
    "name": lambda ctx: ctx["name"],
    "today": lambda _ctx: _dt.date.today().isoformat(),
    "now": lambda _ctx: _dt.datetime.now().strftime("%H:%M"),
}


def render_template(text: str, frontmatter: dict | None,
                    name: str) -> str:
    """替换正文里的 {{key}} 占位符。未知键保留原文。"""
    if not text:
        return text
    ctx = {"name": name}

    # 先移除模板注释
    text = _COMMENT_RE.sub("", text)

    def replace(m: re.Match) -> str:
        key = m.group(1)
        if key in _BUILTIN_RESOLVERS:
            return _BUILTIN_RESOLVERS[key](ctx)
        value = (frontmatter or {}).get(key)
        if value is None:
            return m.group(0)  # 未定义：保留原文
        if isinstance(value, bool):
            return "是" if value else "否"
        if isinstance(value, list):
            return ", ".join(str(v) for v in value)
        return str(value)

    return _PLACEHOLDER_RE.sub(replace, text)


def extract_placeholders(text: str) -> list[str]:
    """正文中出现的全部占位符键名（去重保序）。供模板校验器用。"""
    seen: list[str] = []
    for m in _PLACEHOLDER_RE.finditer(_COMMENT_RE.sub("", text or "")):
        if m.group(1) not in seen:
            seen.append(m.group(1))
    return seen


def undefined_placeholders(text: str, frontmatter: dict | None,
                           name: str) -> list[str]:
    """列出渲染后将仍显示为 {{…}} 的键（= 未定义且非内置）。"""
    rendered = render_template(text, frontmatter, name)
    left = {m.group(1) for m in _PLACEHOLDER_RE.finditer(rendered)}
    return sorted(left)
