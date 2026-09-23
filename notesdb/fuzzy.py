"""模糊匹配（M38）：通用化的名字相似度工具。

suggest 模块内置了编辑距离；导出/导入/命令行补全也需要
"名字打错了给建议"。抽成独立模块：

  levenshtein(a, b)        经典编辑距离（O(mn)）
  jaro_winkler(a, b)       前缀加权的相似度（0-1，适合人名/笔记名）
  best_matches(target, candidates, n, scorer)
                           取前 n 个最相似的候选

两个算法互补：levenshtein 对"改几个字符"敏感（拼写错误），
jaro_winkler 对"前缀对上"给高分（补全场景）。
"""
from __future__ import annotations


def levenshtein(a: str, b: str) -> int:
    """编辑距离（插入/删除/替换各计 1）。"""
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(
                prev[j] + 1,
                cur[j - 1] + 1,
                prev[j - 1] + (ca != cb),
            ))
        prev = cur
    return prev[-1]


def jaro(a: str, b: str) -> float:
    """Jaro 相似度（0-1）。"""
    if a == b:
        return 1.0
    la, lb = len(a), len(b)
    if not la or not lb:
        return 0.0
    window = max(la, lb) // 2 - 1
    if window < 0:
        window = 0
    a_hit = [False] * la
    b_hit = [False] * lb
    matches = 0
    for i in range(la):
        lo = max(0, i - window)
        hi = min(i + window + 1, lb)
        for j in range(lo, hi):
            if not b_hit[j] and a[i] == b[j]:
                a_hit[i] = b_hit[j] = True
                matches += 1
                break
    if not matches:
        return 0.0
    # 顺序一致的匹配数
    transpositions = 0
    k = 0
    for i in range(la):
        if a_hit[i]:
            while not b_hit[k]:
                k += 1
            if a[i] != b[k]:
                transpositions += 1
            k += 1
    transpositions //= 2
    m = matches
    return (m / la + m / lb + (m - transpositions) / m) / 3


def jaro_winkler(a: str, b: str, scale: float = 0.1,
                 max_prefix: int = 4) -> float:
    """Jaro-Winkler：共同前缀加权（前缀匹配在名字场景价值高）。"""
    j = jaro(a, b)
    prefix = 0
    for ca, cb in zip(a[:max_prefix], b[:max_prefix]):
        if ca != cb:
            break
        prefix += 1
    return j + prefix * scale * (1 - j)


def best_matches(target: str, candidates, n: int = 3,
                 scorer=None) -> list[tuple[str, float]]:
    """与 target 最相似的 n 个候选 [(candidate, score)]（降序）。

    默认 scorer 是 jaro_winkler（名字场景）。
    """
    scorer = scorer or jaro_winkler
    scored = [(c, scorer(target, c)) for c in candidates]
    scored.sort(key=lambda x: (-x[1], x[0]))
    return scored[:n]
