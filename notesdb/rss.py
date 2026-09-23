"""RSS 输出（M34）：把最近修改的笔记生成 RSS 2.0 feed。

把导出站点接进 RSS 阅读器：新笔记/更新自动推送到阅读器，
不用主动打开站点。

  build_feed(notes, mtime_fn, base_url, limit=20)
    最近修改的 limit 篇生成 RSS XML（手工拼接，零依赖）；
    base_url 是导出站点地址（item 链接指向导出页）。

转义：XML 实体全转义（笔记内容不可信）。
时间：mtime_fn 注入（测试可控）；RFC 822 格式（RSS 规范）。
"""
from __future__ import annotations

import html
from datetime import UTC, datetime
from email.utils import format_datetime


def build_feed(notes: dict[str, dict], mtime_fn,
               base_url: str, title: str = "notesdb",
               limit: int = 20) -> str:
    """生成 RSS 2.0 XML 文本。"""
    items: list[tuple[str, float]] = []
    for name in notes:
        ts = mtime_fn(name)
        if ts is not None:
            items.append((name, ts))
    items.sort(key=lambda x: -x[1])
    items = items[:limit]


    from .model import note_title

    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<rss version="2.0">', "<channel>",
             f"  <title>{_x(title)}</title>",
             f"  <link>{_x(base_url)}</link>",
             "  <description>最近修改的笔记</description>"]
    for name, ts in items:
        note = notes[name]
        t = note_title(note) or name
        dt = datetime.fromtimestamp(ts, tz=UTC)
        link = f"{base_url.rstrip('/')}/notes/{_href(name)}"
        body = (note.get("body") or "").strip()
        summary = body[:200] + ("…" if len(body) > 200 else "")
        lines += ["  <item>",
                  f"    <title>{_x(t)}</title>",
                  f"    <link>{_x(link)}</link>",
                  f"    <guid>{_x(link)}</guid>",
                  f"    <pubDate>{format_datetime(dt)}</pubDate>",
                  f"    <description>{_x(summary)}</description>",
                  "  </item>"]
    lines += ["</channel>", "</rss>"]
    return "\n".join(lines) + "\n"


def write_feed(root, notes, mtime_fn, base_url: str,
               limit: int = 20) -> str:
    """生成并落盘 export/rss.xml。返回文件路径。"""
    import os

    feed = build_feed(notes, mtime_fn, base_url, limit=limit)
    out_dir = os.path.join(root, "export")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "rss.xml")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(feed)
    return path


def _x(text: str) -> str:
    return html.escape(str(text), quote=True)


def _href(name: str) -> str:
    from urllib.parse import quote

    return quote(f"{name}.html", safe="")
