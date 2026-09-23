"""M41 ANSI 高亮测试。"""
import io

from notesdb.ansi import ansi_highlight, strip_ansi, supports_color


def test_highlight_wraps_match():
    out = ansi_highlight("find quick here", ["quick"])
    assert "\x1b[7;33m" in out and "quick" in out
    assert out.count("\x1b[0m") >= 1


def test_highlight_case_insensitive():
    out = ansi_highlight("PYTHON", ["python"])
    assert "\x1b[7;33m" in out


def test_highlight_chinese():
    out = ansi_highlight("全文检索", ["检索"])
    assert "\x1b[7;33m" in out


def test_highlight_no_terms_plain():
    assert ansi_highlight("plain", []) == "plain"


def test_highlight_word_boundary():
    assert ansi_highlight("category", ["cat"]) == "category"


def test_strip_ansi_roundtrip():
    colored = ansi_highlight("hello world", ["hello"])
    assert strip_ansi(colored) == "hello world"


def test_strip_plain_text_untouched():
    assert strip_ansi("普通文本") == "普通文本"


def test_supports_color_respects_no_color(monkeypatch):
    monkeypatch.setenv("NO_COLOR", "1")
    assert not supports_color(io.StringIO())


def test_supports_color_force(monkeypatch):
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.setenv("FORCE_COLOR", "1")
    assert supports_color(io.StringIO())


def test_supports_color_non_tty():
    assert not supports_color(io.StringIO())  # StringIO 无 isatty=True
