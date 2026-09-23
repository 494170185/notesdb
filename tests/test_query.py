"""M5 查询语言与执行测试。"""
import pytest

from notesdb.query import QueryError, describe, parse_query
from notesdb.runner import run


def _notes():
    return {
        "alpha": {"frontmatter": {"tags": ["work"], "title": "Alpha 计划"},
                  "body": "季度复盘 的记录\n见 [[beta]]"},
        "beta": {"frontmatter": {"tags": ["work", "urgent"]},
                 "body": "project planning notes\n[[alpha]] and [[ghost]]"},
        "gamma": {"frontmatter": {"tags": ["home"]},
                  "body": "shopping list 季度复盘"},
        "delta": {"frontmatter": None, "body": "孤岛笔记没有链接"},
    }


# ---------------------------------------------------------------- 解析

def test_parse_words():
    q = parse_query("hello world")
    assert q.words == ["hello", "world"]


def test_parse_phrase():
    q = parse_query('tag:work "季度 复盘"')
    assert q.phrases == ["季度 复盘"]
    assert q.include_tags == ["work"]


def test_parse_tags():
    q = parse_query("tag:work -tag:archive tag:Urgent")
    assert q.include_tags == ["work", "urgent"]  # 小写化
    assert q.exclude_tags == ["archive"]


def test_parse_link_and_flags():
    q = parse_query("link:beta orphan unresolved")
    assert q.links_to == ["beta"]
    assert q.orphan_only and q.unresolved_only


def test_parse_empty():
    q = parse_query("")
    assert q.is_empty()


def test_parse_empty_tag_raises():
    with pytest.raises(QueryError):
        parse_query("tag:")
    with pytest.raises(QueryError):
        parse_query("-tag:")


def test_describe_readable():
    q = parse_query('tag:work "复盘" -tag:home')
    d = describe(q)
    assert "work" in d and "复盘" in d and "home" in d


# ---------------------------------------------------------------- 执行

def test_run_empty_query_returns_all():
    assert len(run(_notes(), parse_query(""))) == 4


def test_run_word():
    hits = run(_notes(), parse_query("project"))
    assert list(hits) == ["beta"]


def test_run_words_and():
    hits = run(_notes(), parse_query("planning notes"))
    assert list(hits) == ["beta"]


def test_run_phrase():
    hits = run(_notes(), parse_query('"季度复盘"'))
    assert set(hits) == {"alpha", "gamma"}


def test_run_tag_include():
    hits = run(_notes(), parse_query("tag:work"))
    assert set(hits) == {"alpha", "beta"}


def test_run_tag_include_exclude():
    hits = run(_notes(), parse_query("tag:work -tag:urgent"))
    assert list(hits) == ["alpha"]


def test_run_link():
    hits = run(_notes(), parse_query("link:beta"))
    assert list(hits) == ["alpha"]


def test_run_orphan():
    # gamma 与 delta 都没有任何 wikilink（alpha↔beta 互链）
    hits = run(_notes(), parse_query("orphan"))
    assert sorted(hits) == ["delta", "gamma"]


def test_run_unresolved():
    hits = run(_notes(), parse_query("unresolved"))
    assert list(hits) == ["beta"]  # beta 引用 ghost


def test_run_combined():
    hits = run(_notes(), parse_query("tag:work 季度复盘"))
    assert list(hits) == ["alpha"]
