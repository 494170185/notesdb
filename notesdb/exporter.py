"""静态站点导出（M6）：笔记库 → 可离线浏览的 HTML 目录。

结构（export/）：
  index.html        全库索引（按笔记名分组 + 标签侧栏 + 统计）
  notes/<名>.html   每篇笔记（正文 + 反向链接区 + 出链列表）
  tags.html         标签总览（每个标签的笔记列表）
  style.css         样式（内置，无外部依赖）

设计口径：
- 完全离线：不引任何 CDN/外部资源，浏览器直接打开可用；
- 笔记名即文件名（URL 编码），wikilink 交叉链接；
- 悬空链接渲染为红字（不生成 404 页面——它本来就不存在）；
- 覆盖式导出：每次全量重建 export/（笔记库是小数据源，
  增量同步的复杂度不值得）。
"""
from __future__ import annotations

import shutil
from pathlib import Path
from urllib.parse import quote

from .links import LinkGraph, build_graph
from .model import note_title
from .render import render_markdown
from .tags import build_tag_index, note_tags

EXPORT_DIRNAME = "export"
NOTES_SUBDIR = "notes"

_STYLE_CSS = """\
:root { --bg:#fafafa; --fg:#1a1a2e; --muted:#6a6a7a; --card:#ffffff;
        --border:#e2e2ea; --accent:#4a5fc1; --danger:#c14a4a; }
* { box-sizing: border-box; margin:0; }
body { font-family:"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;
       background:var(--bg); color:var(--fg); line-height:1.65; padding:24px; }
.container { max-width:820px; margin:0 auto; }
header.site { margin-bottom:20px; }
header.site h1 { font-size:22px; }
header.site p { color:var(--muted); font-size:13px; }
.card { background:var(--card); border:1px solid var(--border);
        border-radius:10px; padding:18px 20px; margin-bottom:14px; }
h1.note-title { font-size:24px; margin-bottom:12px; }
.meta { color:var(--muted); font-size:12.5px; margin-bottom:16px; }
.meta .tag { display:inline-block; background:#eef0fa; color:var(--accent);
             padding:1px 9px; border-radius:999px; margin:0 4px 0 2px; }
nav.backlinks { margin-top:22px; }
nav.backlinks h2 { font-size:14px; color:var(--muted); margin-bottom:6px; }
nav.backlinks ul { list-style:none; font-size:13.5px; }
nav.backlinks a, a.wikilink { color:var(--accent); text-decoration:none; }
a:hover { text-decoration:underline; }
.wikilink.dangling { color:var(--danger); border-bottom:1px dotted var(--danger); }
pre { background:#f0f0f5; padding:12px; border-radius:8px;
      overflow-x:auto; font-size:13px; }
code { background:#f0f0f5; padding:1px 5px; border-radius:4px; font-size:0.92em; }
ul.index { list-style:none; }
ul.index li { padding:5px 0; border-bottom:1px solid var(--border); font-size:14.5px; }
.stats { display:flex; gap:18px; color:var(--muted); font-size:12.5px;
         margin-bottom:14px; flex-wrap:wrap; }
a.home { font-size:12.5px; color:var(--accent); text-decoration:none; }
footer { text-align:center; color:var(--muted); font-size:11.5px; margin-top:26px; }
"""


def export_site(root: str | Path, notes: dict[str, dict],
                graph: LinkGraph | None = None) -> Path:
    """全量导出。返回 export/ 路径。"""
    root = Path(root)
    out_dir = root / EXPORT_DIRNAME
    graph = graph or build_graph(notes)
    existing = set(notes)

    # 覆盖式重建（保留目录本身，防 Windows 上 rmtree 与打开的句柄冲突）
    if out_dir.exists():
        shutil.rmtree(out_dir, ignore_errors=True)
    (out_dir / NOTES_SUBDIR).mkdir(parents=True, exist_ok=True)

    # 样式
    (out_dir / "style.css").write_text(_STYLE_CSS, encoding="utf-8")

    # 每篇笔记
    for name, note in sorted(notes.items()):
        _export_note(out_dir, name, note, graph, existing)

    # 索引页
    (out_dir / "index.html").write_text(
        _page("全部笔记", _index_body(notes, graph)), encoding="utf-8")

    # 标签页
    tag_index = build_tag_index(notes)
    (out_dir / "tags.html").write_text(
        _page("标签", _tags_body(tag_index)), encoding="utf-8")

    return out_dir


def _page(title: str, body_html: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{_esc(title)}</title>
<link rel="stylesheet" href="style.css">
</head>
<body>
<div class="container">
<header class="site">
  <h1>{_esc(title)}</h1>
  <p><a class="home" href="index.html">索引</a> · <a class="home" href="tags.html">标签</a></p>
</header>
{body_html}
<footer>notesdb 静态导出 · 离线可用</footer>
</div>
</body>
</html>"""


def _index_body(notes: dict[str, dict], graph: LinkGraph) -> str:
    items = []
    for name in sorted(notes):
        note = notes[name]
        title = note_title(note) or name
        tags = note_tags(note)
        tag_html = "".join(f'<span class="tag">{_esc(t)}</span>' for t in tags)
        bl = len(graph.backlinks(name))
        items.append(
            f'<li><a href="notes/{_href(name)}">{_esc(name)}</a>'
            f" — {_esc(title)}{tag_html}"
            f' <span style="color:var(--muted)">被引 {bl}</span></li>')
    stats = (f'<div class="stats"><span>笔记 {len(notes)}</span>'
             f'<span>悬空链接 {len(graph.unresolved)}</span>'
             f'<span>孤岛 {len(graph.orphans(list(notes)))}</span></div>')
    return stats + '<ul class="index">' + "".join(items) + "</ul>"


def _tags_body(tag_index: dict[str, list[str]]) -> str:
    if not tag_index:
        return '<p style="color:var(--muted)">没有标签。</p>'
    parts = []
    for tag, names in tag_index.items():
        links = ", ".join(
            f'<a href="notes/{_href(n)}">{_esc(n)}</a>' for n in names)
        parts.append(f'<div class="card"><strong>{_esc(tag)}</strong>'
                     f'<span style="color:var(--muted)"> ({len(names)})</span>'
                     f"<div>{links}</div></div>")
    return "".join(parts)


def _export_note(out_dir: Path, name: str, note: dict,
                 graph: LinkGraph, existing: set[str]) -> None:
    from .template import render_template

    title = note_title(note) or name
    # 模板变量先于 Markdown 渲染（占位符可能生成 markdown 结构）
    body_text = render_template(note.get("body", ""),
                                note.get("frontmatter"), name)
    body = render_markdown(body_text, existing)
    tags = note_tags(note)
    tag_html = "".join(f'<span class="tag">{_esc(t)}</span>' for t in tags)

    # 反向链接（谁引用了我）与出链（我引用了谁）
    backlinks = graph.backlinks(name)
    bl_html = ""
    if backlinks:
        items = "".join(f'<li><a href="{_href(b)}">{_esc(b)}</a></li>'
                        for b in backlinks)
        bl_html = f'<nav class="backlinks"><h2>反向链接（{len(backlinks)}）</h2><ul>{items}</ul></nav>'

    outgoing = [t for t in graph.outgoing.get(name, [])]
    out_html = ""
    if outgoing:
        items = "".join(
            f'<li><a href="{_href(t)}">{_esc(t)}</a></li>' if t in existing
            else f'<li><span class="wikilink dangling">{_esc(t)}</span></li>'
            for t in outgoing)
        out_html = f'<nav class="backlinks"><h2>出链（{len(outgoing)}）</h2><ul>{items}</ul></nav>'

    html_doc = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{_esc(title)}</title>
<link rel="stylesheet" href="../style.css">
</head>
<body>
<div class="container">
<header class="site">
  <h1 class="note-title">{_esc(title)}</h1>
  <p><a class="home" href="../index.html">← 索引</a></p>
</header>
<div class="meta">{tag_html}</div>
<div class="card">
{body}
</div>
{bl_html}
{out_html}
<footer>notesdb 静态导出</footer>
</div>
</body>
</html>"""
    (out_dir / NOTES_SUBDIR / f"{name}.html").write_text(
        html_doc, encoding="utf-8")


def _href(name: str) -> str:
    return quote(f"{name}.html", safe="")


def _esc(s: str) -> str:
    import html

    return html.escape(str(s))
