"""轻量 Markdown → HTML 渲染（M6）。

只覆盖笔记场景的常见语法（不追 CommonMark 全集）：
  标题 #/##/###、无序/有序列表、代码块、行内代码、粗体、斜体、
  链接 [t](u)、wikilink [[x]]、段落、水平线。

安全口径：**全部文本先 HTML 转义再拼结构**——笔记内容是
不可信输入（可能从任何地方粘贴来），导出的 HTML 会被浏览器
直接打开，XSS 面必须封死。转义发生在 _esc()，所有文本路径
都过它，不允许裸拼。

wikilink 是渲染层的扩展：[[目标]] → 存在则链接到导出页，
不存在则红字（悬空链接可视化）。
"""
from __future__ import annotations

import html
import re

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
_ULIST_RE = re.compile(r"^\s*[-*+]\s+(.*)$")
_OLIST_RE = re.compile(r"^\s*\d+[.)]\s+(.*)$")
_FENCE_RE = re.compile(r"^\s*(```|~~~)")
_HR_RE = re.compile(r"^\s*(-{3,}|\*{3,})\s*$")

_WIKILINK_RE = re.compile(r"\[\[([^\]\n|]+)(?:\|[^\]\n]*)?\]\]")
_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
_BOLD_RE = re.compile(r"\*\*([^*\n]+)\*\*")
_ITALIC_RE = re.compile(r"(?<!\*)\*([^*\n]+)\*(?!\*)")
_CODE_RE = re.compile(r"`([^`\n]+)`")


def render_markdown(body: str, existing: set[str] | None = None) -> str:
    """渲染正文为 HTML 片段。existing = 库里存在的笔记名集合
    （决定 wikilink 渲染成链接还是红字）。"""
    existing = existing or set()
    out: list[str] = []
    lines = (body or "").splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]

        if _FENCE_RE.match(line):
            fence = line.strip()[:3]
            code_lines: list[str] = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith(fence):
                code_lines.append(lines[i])
                i += 1
            i += 1  # 跳过闭合围栏（若有）
            out.append("<pre><code>" + html.escape("\n".join(code_lines)) + "</code></pre>")
            continue

        m = _HEADING_RE.match(line)
        if m:
            level = min(len(m.group(1)) + 1, 6)  # 页面 h1 留给笔记名
            out.append(f"<h{level}>{_inline(m.group(2), existing)}</h{level}>")
            i += 1
            continue

        if _HR_RE.match(line):
            out.append("<hr>")
            i += 1
            continue

        ul_match = _ULIST_RE.match(line)
        ol_match = _OLIST_RE.match(line)
        if ul_match or ol_match:
            tag = "ul" if ul_match else "ol"
            items: list[str] = []
            item_re = _ULIST_RE if ul_match else _OLIST_RE
            while i < len(lines) and (im := item_re.match(lines[i])):
                items.append(f"<li>{_inline(im.group(1), existing)}</li>")
                i += 1
            out.append(f"<{tag}>" + "".join(items) + f"</{tag}>")
            continue

        if line.strip():
            para: list[str] = [line]
            i += 1
            while i < len(lines) and lines[i].strip() \
                    and not _HEADING_RE.match(lines[i]) \
                    and not _FENCE_RE.match(lines[i]) \
                    and not _ULIST_RE.match(lines[i]) \
                    and not _OLIST_RE.match(lines[i]):
                para.append(lines[i])
                i += 1
            out.append("<p>" + _inline("\n".join(para), existing) + "</p>")
            continue

        i += 1
    return "\n".join(out)


def _inline(text: str, existing: set[str]) -> str:
    """行内元素渲染。先挖出行内代码（其中不再解析其他语法）。"""
    parts: list[tuple[str, bool]] = []  # (content, is_code)
    last = 0
    for m in _CODE_RE.finditer(text):
        parts.append((text[last:m.start()], False))
        parts.append((m.group(1), True))
        last = m.end()
    parts.append((text[last:], False))

    rendered: list[str] = []
    for content, is_code in parts:
        if is_code:
            rendered.append(f"<code>{html.escape(content)}</code>")
        else:
            rendered.append(_inline_no_code(content, existing))
    return "".join(rendered)


def _inline_no_code(text: str, existing: set[str]) -> str:
    s = html.escape(text)
    # 链接 [t](u)：u 只允许 http/https/#/相对路径
    s = _LINK_RE.sub(lambda m: _safe_link(m.group(1), m.group(2)), s)
    # wikilink（转义后 [[ 不变形，因为 [ ] 都不是 HTML 特殊字符）
    s = _WIKILINK_RE.sub(
        lambda m: _wikilink_html(m.group(1).strip(), existing), s)
    s = _BOLD_RE.sub(r"<strong>\1</strong>", s)
    s = _ITALIC_RE.sub(r"<em>\1</em>", s)
    return s


_ALLOWED_URL_PREFIXES = ("http://", "https://", "#", "/", "./", "../")
_DANGEROUS_URL_PREFIXES = ("javascript:", "data:", "vbscript:", "file:")


def _safe_link(text: str, url: str) -> str:
    """链接白名单：相对路径与 http(s)/锚点放行，危险协议降级纯文本。"""
    low = url.lower().strip()
    if low.startswith(_DANGEROUS_URL_PREFIXES):
        return html.escape(f"{text} ({url})")
    if low.startswith(_ALLOWED_URL_PREFIXES) or "://" not in low:
        return f'<a href="{html.escape(url, quote=True)}">{html.escape(text)}</a>'
    # 其他自定义协议（mailto: 之外的 ftp: 等）保守起见也放行外链语义
    if low.startswith("mailto:"):
        return f'<a href="{html.escape(url, quote=True)}">{html.escape(text)}</a>'
    return html.escape(f"{text} ({url})")


def _wikilink_html(target: str, existing: set[str]) -> str:
    if target in existing:
        href = html.escape(_note_href(target), quote=True)
        return f'<a class="wikilink" href="{href}">{html.escape(target)}</a>'
    return f'<span class="wikilink dangling">{html.escape(target)}</span>'


def _note_href(name: str) -> str:
    """笔记名的导出相对链接（URL 编码，跨子目录安全）。"""
    from urllib.parse import quote

    return quote(f"notes/{name}.html", safe="/")
