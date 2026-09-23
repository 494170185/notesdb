"""M7 模板变量测试。"""
import datetime as dt

from notesdb.template import (
    extract_placeholders,
    render_template,
    undefined_placeholders,
)


def test_simple_substitution():
    out = render_template("项目 {{project}} 结束", {"project": "Aurora"}, "n")
    assert out == "项目 Aurora 结束"


def test_builtin_name():
    out = render_template("我是 {{name}}", None, "周报-03")
    assert out == "我是 周报-03"


def test_builtin_today_format():
    out = render_template("日期 {{today}}", None, "n").removeprefix("日期 ").strip()
    assert dt.date.fromisoformat(out) == dt.date.today()  # 合法 ISO 日期


def test_builtin_now_format():
    out = render_template("时刻 {{now}}", None, "n").removeprefix("时刻 ").strip()
    hh, mm = out.split(":")
    assert 0 <= int(hh) < 24 and 0 <= int(mm) < 60


def test_undefined_key_kept_verbatim():
    out = render_template("缺 {{missing}} 变量", {"x": 1}, "n")
    assert "{{missing}}" in out


def test_comment_removed():
    out = render_template("a {{# 内部说明 }}b", None, "n")
    assert out == "a b"


def test_list_value_joined():
    out = render_template("成员：{{members}}", {"members": ["甲", "乙"]}, "n")
    assert out == "成员：甲, 乙"


def test_bool_value_localized():
    assert render_template("{{done}}", {"done": True}, "n") == "是"
    assert render_template("{{done}}", {"done": False}, "n") == "否"


def test_number_value():
    assert render_template("第 {{n}} 期", {"n": 3}, "n") == "第 3 期"


def test_spaces_around_key_tolerated():
    assert render_template("{{  x  }}", {"x": "ok"}, "n") == "ok"


def test_extract_placeholders_dedup_order():
    keys = extract_placeholders("{{a}} {{b}} {{a}}")
    assert keys == ["a", "b"]


def test_extract_ignores_comments():
    keys = extract_placeholders("{{# 说明 }} {{real}}")
    assert keys == ["real"]


def test_undefined_placeholders_listing():
    text = "{{known}} 与 {{unknown1}} {{unknown2}}"
    left = undefined_placeholders(text, {"known": 1}, "n")
    assert left == ["unknown1", "unknown2"]


def test_empty_text():
    assert render_template("", None, "n") == ""
