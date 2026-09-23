"""M18 性能基准测试（小规模验证正确性，不等时长的真实基准）。

基准本身在 CI 里跑（tests/test_bench_ci.py 标记 slow），
这里只验证：合成数据形状、计时字段齐全、预算断言逻辑。
"""
import pytest

from notesdb.bench import (
    BUDGETS,
    assert_budget,
    bench,
    synth_notes,
)


def test_synth_notes_deterministic():
    a = synth_notes(50)
    b = synth_notes(50)
    assert a == b


def test_synth_notes_shape():
    notes = synth_notes(30)
    assert len(notes) == 30
    note = notes["note5"]
    assert note["frontmatter"]["tags"]
    assert "[[" in note["body"]  # 有 wikilink
    assert "word" in note["body"]


def test_bench_returns_all_ops():
    # 小库跑真实基准（毫秒级），只验证字段齐全
    results = bench(synth_notes(20))
    assert set(results) == set(BUDGETS)
    assert all(v >= 0 for v in results.values())


def test_assert_budget_passes_within():
    assert_budget({"build_index": 0.001})  # 远小于预算


def test_assert_budget_fails_over():
    with pytest.raises(AssertionError, match="build_index"):
        assert_budget({"build_index": 999.0})


def test_assert_budget_ignores_missing_ops():
    assert_budget({})  # 没跑的项不比对


def test_assert_budget_custom():
    with pytest.raises(AssertionError):
        assert_budget({"tokenize": 2.0}, budgets={"tokenize": 1.0})
