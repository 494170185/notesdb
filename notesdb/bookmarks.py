"""URL 收集（M28）：把笔记里出现的外部链接整理成书签库。

写笔记时随手贴的链接散落各篇，需要时找不到。本模块把
全部 http(s) 链接提取、去重、按域名分组：

  extract_urls(body)          [(url, 行号)]
  collect(notes)              {url: [出现笔记]}（URL 去重）
  by_domain(urls)             {domain: [url]}（域名分组）
  render_bookmarks(notes)     Markdown 书签页正文

提取口径与 refs 模块互补：那边只管本地路径，这边只管 http(s)。
裸 URL（不在 []() 里的）也收——笔记里"见 https://x.com"很常见。
"""
from __future__ import annotations

import re
from urllib.parse import urlparse

# Markdown 链接形态的 URL + 裸 URL
_MD_URL_RE = re.compile(r"\]\((https?://[^)\s]+)\)")
_BARE_URL_RE = re.compile(r"(?<!\(\s)(https?://[^\s<>)\"'\]]+)")


def extract_urls(body: str) -> list[tuple[str, int]]:
    """正文中的 http(s) 链接 [(url, line)]，保持出现顺序。"""
    out: list[tuple[str, int]] = []
    for line_no, line in enumerate((body or "").splitlines()):
        # 行内代码里的 URL 不收（示例链接不是真引用）
        stripped = re.sub(r"`[^`\n]*`", " ", line)
        seen_line: set[str] = set()
        for m in _MD_URL_RE.finditer(stripped):
            url = _clean(m.group(1))
            if url and url not in seen_line:
                seen_line.add(url)
                out.append((url, line_no))
        for m in _BARE_URL_RE.finditer(stripped):
            url = _clean(m.group(1))
            if url and url not in seen_line:
                seen_line.add(url)
                out.append((url, line_no))
    return out


def _clean(url: str) -> str:
    # 中英文句读都剥（URL 里不会出现这些字符）
    return url.rstrip(".,;:!?)]}）】》\"'”’。，；！？、").strip()


def collect(notes: dict[str, dict]) -> dict[str, list[str]]:
    """全部链接 {url: [出现笔记]}（笔记名排序去重）。"""
    found: dict[str, set[str]] = {}
    for name, note in sorted(notes.items()):
        for url, _ in extract_urls(note.get("body", "")):
            found.setdefault(url, set()).add(name)
    return {url: sorted(names) for url, names in sorted(found.items())}


def by_domain(urls) -> dict[str, list[str]]:
    """URL 列表按域名分组（域名升序、组内保持输入序）。"""
    groups: dict[str, list[str]] = {}
    for url in urls:
        domain = urlparse(url).netloc or "(无域名)"
        groups.setdefault(domain, []).append(url)
    return dict(sorted(groups.items()))


def render_bookmarks(notes: dict[str, dict]) -> str:
    """Markdown 书签页（按域名分组，每条带来源笔记）。"""
    collected = collect(notes)
    if not collected:
        return "# 书签\n\n（暂无外部链接）\n"
    lines = ["# 书签", ""]
    for domain, urls in by_domain(collected).items():
        lines.append(f"## {domain}")
        lines.append("")
        for url in urls:
            sources = collected[url]
            src = "、".join(f"[[{s}]]" for s in sources)
            lines.append(f"- {url}（来自 {src}）")
        lines.append("")
    return "\n".join(lines) + "\n"
