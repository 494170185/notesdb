"""M28 URL 收集测试。"""
from notesdb.bookmarks import (
    by_domain,
    collect,
    extract_urls,
    render_bookmarks,
)

# ---------------------------------------------------------------- 提取

def test_extract_markdown_link():
    urls = extract_urls("看 [官网](https://example.com) 哈")
    assert urls == [("https://example.com", 0)]


def test_extract_bare_url():
    urls = extract_urls("参考 https://example.com/page 说明")
    assert urls == [("https://example.com/page", 0)]


def test_extract_dedupes_per_line():
    urls = extract_urls("[a](https://x.com) 及 https://x.com")
    assert urls == [("https://x.com", 0)]


def test_extract_trailing_punctuation():
    assert extract_urls("见 https://x.com。")[0][0] == "https://x.com"


def test_extract_ignores_inline_code():
    assert extract_urls("运行 `pip install https://evil` 时") == []


def test_extract_line_numbers():
    urls = extract_urls("a\nb\nhttps://x.com\n")
    assert urls[0][1] == 2


def test_extract_empty():
    assert extract_urls("") == []


def test_extract_only_http_s():
    assert extract_urls("ftp://x.com mailto:a@b") == []


# ---------------------------------------------------------------- 收集

def test_collect_groups_by_url():
    notes = {
        "a": {"body": "https://x.com 与 [l](https://y.com)\n"},
        "b": {"body": "又见 https://x.com\n"},
    }
    out = collect(notes)
    assert out["https://x.com"] == ["a", "b"]
    assert out["https://y.com"] == ["a"]


def test_collect_empty():
    assert collect({}) == {}


# ---------------------------------------------------------------- 域名分组

def test_by_domain():
    groups = by_domain(["https://a.com/1", "https://b.com/x", "https://a.com/2"])
    assert groups == {"a.com": ["https://a.com/1", "https://a.com/2"],
                      "b.com": ["https://b.com/x"]}


# ---------------------------------------------------------------- 渲染

def test_render_bookmarks_content():
    notes = {"a": {"body": "https://x.com\n"}}
    md = render_bookmarks(notes)
    assert "# 书签" in md
    assert "x.com" in md
    assert "[[a]]" in md


def test_render_bookmarks_empty():
    md = render_bookmarks({})
    assert "暂无外部链接" in md
