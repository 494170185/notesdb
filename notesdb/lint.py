"""库健康校验（M8）：对整个笔记库跑一致性检查，输出结构化问题清单。

检查项（每项都对应真实用户痛的一个）：
  bad_frontmatter   frontmatter 块存在但 YAML 解析失败
  empty_note        正文为空（只剩 frontmatter 的空壳笔记）
  title_dup         两篇笔记 title 相同（索引页难以区分）
  dangling_links    悬空链接清单（提示但不算错——是特性，
                    仅当链接密度异常时值得关注）
  orphan_notes      孤岛笔记（没有任何链接关系）
  broken_template   模板占位符渲染后仍保留（未定义的 key）
  name_conflict    大小写不同的两个笔记名（Windows 不区分大小写，
                    跨平台同步会炸）

返回 list[Issue]，严重级（error）问题导致 CLI 退出码 1，
提示级（warning）不影响。规则：坏 frontmatter/名字冲突是 error，
其余是 warning（笔记本来就是渐进写作，空壳与孤岛合法存在）。
"""
from __future__ import annotations

from dataclasses import dataclass

from .links import build_graph
from .model import note_title
from .template import undefined_placeholders


@dataclass
class Issue:
    severity: str   # "error" | "warning"
    check: str
    note: str       # 相关笔记名（"" = 库级问题）
    message: str

    def __str__(self) -> str:
        head = f"[{self.severity}] {self.check}"
        return f"{head} {self.note}: {self.message}" if self.note \
            else f"{head}: {self.message}"


def check_library(notes: dict[str, dict]) -> list[Issue]:
    """跑全部检查，返回问题列表（空 = 健康）。"""
    issues: list[Issue] = []
    issues.extend(_check_frontmatter(notes))
    issues.extend(_check_empty(notes))
    issues.extend(_check_title_dup(notes))
    issues.extend(_check_name_conflict(notes))
    issues.extend(_check_templates(notes))

    graph = build_graph(notes)
    for target in graph.unresolved:
        sources = [n for n, ts in graph.outgoing.items() if target in ts]
        issues.append(Issue("warning", "dangling_links", sources[0] if len(sources) == 1 else "",
                            f"悬空链接 [[{target}]]（{len(sources)} 篇引用）"))
    for orphan in graph.orphans(list(notes)):
        issues.append(Issue("warning", "orphan_notes", orphan,
                            "孤岛笔记（无任何链接关系）"))
    return issues


def has_errors(issues: list[Issue]) -> bool:
    return any(i.severity == "error" for i in issues)


def _check_frontmatter(notes: dict[str, dict]) -> list[Issue]:
    return [Issue("error", "bad_frontmatter", name,
                  "frontmatter 块存在但 YAML 解析失败")
            for name, note in sorted(notes.items())
            if note.get("frontmatter_error")]


def _check_empty(notes: dict[str, dict]) -> list[Issue]:
    return [Issue("warning", "empty_note", name, "正文为空")
            for name, note in sorted(notes.items())
            if not (note.get("body") or "").strip()]


def _check_title_dup(notes: dict[str, dict]) -> list[Issue]:
    by_title: dict[str, list[str]] = {}
    for name, note in sorted(notes.items()):
        title = note_title(note)
        if title:
            by_title.setdefault(title, []).append(name)
    return [Issue("warning", "title_dup", "", f"title {t!r} 重复：{names}")
            for t, names in sorted(by_title.items()) if len(names) > 1]


def _check_name_conflict(notes: dict[str, dict]) -> list[Issue]:
    lowered: dict[str, list[str]] = {}
    for name in sorted(notes):
        lowered.setdefault(name.lower(), []).append(name)
    return [Issue("error", "name_conflict", "",
                  f"大小写冲突：{names}（跨平台同步不安全）")
            for names in sorted(lowered.values()) if len(names) > 1]


def _check_templates(notes: dict[str, dict]) -> list[Issue]:
    out = []
    for name, note in sorted(notes.items()):
        undefined = undefined_placeholders(
            note.get("body", ""), note.get("frontmatter"), name)
        if undefined:
            out.append(Issue("warning", "broken_template", name,
                             f"未定义占位符: {undefined}"))
    return out
