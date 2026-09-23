"""MOC 自动生成（M22）：Map of Content——按链接结构给库建枢纽页。

MOC 是双链笔记的目录页：一个主题下汇入相关笔记的链接。
手工维护容易漏，这里按结构自动生成：

  hub_candidates(notes)   被引最多的笔记（已是事实枢纽）
  cluster_mocs(notes)     按标签聚类生成 MOC 草稿
                        （同标签 ≥3 篇才值得建页，避免一两个
                        笔记也生成空目录）
  render_moc(title, names)  MOC 页正文（wikilink 列表）

输出是草稿文本：写不写库由用户决定（build_moc_note 只生成
不落盘，写入走 edit/new 走既有路径）。
"""
from __future__ import annotations

from .links import build_graph
from .tags import build_tag_index

MIN_CLUSTER = 3  # 标签下至少几篇才值得建 MOC


def hub_candidates(notes: dict[str, dict], top: int = 5) -> list[dict]:
    """被引用最多的笔记（事实枢纽，适合做成 MOC）。"""
    graph = build_graph(notes)
    ranked = sorted(
        ((name, len(graph.backlinks(name))) for name in notes),
        key=lambda x: (-x[1], x[0]))
    return [{"name": n, "backlinks": c} for n, c in ranked[:top] if c > 0]


def cluster_mocs(notes: dict[str, dict],
                 min_cluster: int = MIN_CLUSTER) -> dict[str, list[str]]:
    """按标签聚类的 MOC 草稿：{moc_title: [note names]}。

  标签名直接做 MOC 标题（tag → "MOC: tag"）。
    """
    tag_index = build_tag_index(notes)
    return {f"MOC: {tag}": names
            for tag, names in tag_index.items()
            if len(names) >= min_cluster}


def render_moc(title: str, names: list[str]) -> str:
    """MOC 页正文（草稿文本）。"""
    lines = [f"# {title}", ""]
    if names:
        lines.append("相关笔记：")
        lines.append("")
        lines.extend(f"- [[{n}]]" for n in sorted(names))
    else:
        lines.append("（暂无成员）")
    return "\n".join(lines) + "\n"


def build_moc_note(moc_title: str, names: list[str]) -> dict:
    """MOC 的笔记 dict（不落盘——写入由调用方决定）。"""
    return {
        "frontmatter": {"title": moc_title, "tags": ["moc"]},
        "body": render_moc(moc_title, names),
    }
