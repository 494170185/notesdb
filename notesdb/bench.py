"""性能基准（M18）：各核心操作在合成数据上的吞吐量。

目的不是绝对数字，是**回归探测器**：仓库演进中某个改动让
索引构建慢了 10 倍，CI 里跑一次基准、与阈值比对就能抓到。

基准项（合成笔记，RFC-ish 数据无真实内容）：
  build_index     N 篇笔记建倒排索引
  build_graph     N 篇建链接图
  similar_pairs   N 篇两两相似度
  tokenize        纯文本词元化

bench(notes) 返回 {op: seconds}；assert_budget(actuals, budget)
把结果与预算 dict 对比，超预算抛 AssertionError（CI 断言用）。
"""
from __future__ import annotations

import time

# CI 预算（秒）。留了 5 倍裕量：CI 机器性能方差大于本地。
BUDGETS = {
    "build_index": 2.0,
    "build_graph": 1.0,
    "similar_pairs": 3.0,
    "tokenize": 0.5,
}

NOTE_COUNT = 300
WORDS_PER_NOTE = 60
LINKS_PER_NOTE = 3

_WORDS = [f"word{i}" for i in range(500)]
_CN = "这是用于基准测试的合成中文内容没有真实语义"


def synth_notes(count: int = NOTE_COUNT) -> dict[str, dict]:
    """生成合成笔记（确定性：不随随机数变化，基准可比）。"""
    notes = {}
    for i in range(count):
        words = " ".join(_WORDS[(i * 7 + k) % len(_WORDS)]
                         for k in range(WORDS_PER_NOTE))
        links = " ".join(f"[[note{(i * 13 + k) % count}]]"
                         for k in range(LINKS_PER_NOTE))
        notes[f"note{i}"] = {
            "frontmatter": {"tags": [f"tag{i % 20}"]},
            "body": f"{words}\n{_CN}\n{links}\n",
        }
    return notes


def bench(notes: dict[str, dict]) -> dict[str, float]:
    """跑全部基准，返回 {op: 耗时秒}。"""
    from .index import InvertedIndex
    from .links import build_graph
    from .similar import similar_pairs
    from .tokenize import tokenize

    results: dict[str, float] = {}

    t0 = time.perf_counter()
    idx = InvertedIndex()
    idx.build(notes)
    results["build_index"] = time.perf_counter() - t0

    t0 = time.perf_counter()
    build_graph(notes)
    results["build_graph"] = time.perf_counter() - t0

    t0 = time.perf_counter()
    similar_pairs(notes, threshold=0.3)
    results["similar_pairs"] = time.perf_counter() - t0

    body = notes[f"note0"]["body"]
    t0 = time.perf_counter()
    for _ in range(100):
        tokenize(body)
    results["tokenize"] = time.perf_counter() - t0

    return {k: round(v, 4) for k, v in results.items()}


def assert_budget(actuals: dict[str, float],
                  budgets: dict[str, float] | None = None) -> None:
    """超预算抛 AssertionError（CI 断言）。"""
    budgets = budgets or BUDGETS
    for op, budget in budgets.items():
        actual = actuals.get(op)
        if actual is not None and actual > budget:
            raise AssertionError(
                f"基准超预算: {op} 用时 {actual}s > 预算 {budget}s")
