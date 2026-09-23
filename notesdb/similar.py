"""相似笔记（M13）：按词元重合度推荐相关笔记。

算法：Jaccard 相似度 = |词元集 ∩| / |词元集 ∪|。
- 每篇笔记的词元集合（去重）一次构建；
- 相似度矩阵只对「有共同词元」的笔记对计算（稀疏倒排：
  词元 → 笔记列表，对每个词元的共现对累计交集大小），
  库大时避免 O(n²) 全对比；
- 阈值默认 0.2（两篇笔记有 1/5 词元重合已经算"有关"，
  笔记语料的常用词污染使精确阈值无意义，可调）。

用途：导出页的"相关笔记"区（M6 之后接入）、CLI 的 similar 命令。
"""
from __future__ import annotations

from collections import defaultdict

from .tokenize import tokenize

DEFAULT_THRESHOLD = 0.2


def note_token_set(note: dict) -> set[str]:
    """笔记的词元集合（正文，不含标题——标题相似太浅）。"""
    return set(tokenize(note.get("body", "")))


def build_token_sets(notes: dict[str, dict]) -> dict[str, set[str]]:
    return {name: note_token_set(note) for name, note in notes.items()}


def similar_pairs(notes: dict[str, dict],
                  threshold: float = DEFAULT_THRESHOLD,
                  top: int | None = None) -> list[tuple[str, str, float]]:
    """全部相似笔记对（按相似度降序）。

    返回 [(name_a, name_b, similarity)]，a < b（字典序）保证
    每对只出现一次。
    """
    token_sets = build_token_sets(notes)

    # 稀疏交集：词元 → 出现的笔记，共现对累计交集
    by_token: dict[str, list[str]] = defaultdict(list)
    for name, tokens in sorted(token_sets.items()):
        for t in tokens:
            by_token[t].append(name)

    overlap: dict[tuple[str, str], int] = defaultdict(int)
    for names in by_token.values():
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                overlap[(names[i], names[j])] += 1

    # Jaccard = 交集 / 并集
    results: list[tuple[str, str, float]] = []
    for (a, b), inter in overlap.items():
        union = len(token_sets[a]) + len(token_sets[b]) - inter
        if union <= 0:
            continue
        sim = inter / union
        if sim >= threshold:
            results.append((a, b, round(sim, 4)))

    results.sort(key=lambda x: (-x[2], x[0], x[1]))
    return results[:top] if top else results


def similar_to(name: str, notes: dict[str, dict],
               threshold: float = DEFAULT_THRESHOLD,
               top: int = 5) -> list[tuple[str, float]]:
    """与指定笔记最相似的其他笔记（降序，最多 top 个）。"""
    if name not in notes:
        raise ValueError(f"笔记不存在: {name}")
    pairs = similar_pairs(notes, threshold=threshold)
    out: list[tuple[str, float]] = []
    for a, b, sim in pairs:
        if a == name:
            out.append((b, sim))
        elif b == name:
            out.append((a, sim))
    return out[:top]
