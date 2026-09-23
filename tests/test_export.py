"""M6 渲染器与静态导出测试。"""
import re
from pathlib import Path

from notesdb.exporter import export_site
from notesdb.render import render_markdown


# ---------------------------------------------------------------- 渲染

def test_heading():
    html = render_markdown("## 标题二")
    assert "<h3>标题二</h3>" in html


def test_paragraph():
    assert "<p>hello</p>" in render_markdown("hello")


def test_unordered_list():
    html = render_markdown("- a\n- b")
    assert html.startswith("<ul>")
    assert "<li>a</li><li>b</li>" in html


def test_ordered_list():
    html = render_markdown("1. a\n2. b")
    assert html.startswith("<ol>")


def test_code_block_escaped():
    html = render_markdown("```\n<script>alert(1)</script>\n```")
    assert "&lt;script&gt;" in html
    assert "<script>alert" not in html


def test_inline_code():
    assert "<code>x = 1</code>" in render_markdown("`x = 1`")


def test_inline_code_not_parsed_further():
    """行内代码里的 **bold** 不渲染。"""
    html = render_markdown("`**bold**`")
    assert "<strong>" not in html


def test_bold_and_italic():
    html = render_markdown("**粗** and *斜*")
    assert "<strong>粗</strong>" in html and "<em>斜</em>" in html


def test_wikilink_existing():
    html = render_markdown("[[目标]]", existing={"目标"})
    assert '<a class="wikilink" href="notes/%E7%9B%AE%E6%A0%87.html">目标</a>' in html


def test_wikilink_dangling():
    html = render_markdown("[[不存在]]", existing=set())
    assert '<span class="wikilink dangling">不存在</span>' in html


def test_wikilink_alias_uses_target():
    html = render_markdown("[[目标|别名]]", existing={"目标"})
    assert ">目标</a>" in html


def test_xss_in_text_escaped():
    html = render_markdown("<img src=x onerror=alert(1)>")
    assert "<img" not in html
    assert "&lt;img" in html


def test_dangerous_link_protocol_neutralized():
    html = render_markdown("[点我](javascript:alert(1))")
    assert "<a href=" not in html


def test_http_link_allowed():
    html = render_markdown("[site](https://example.com)")
    assert 'href="https://example.com"' in html


def test_relative_link_allowed():
    html = render_markdown("[go](other.html)")
    assert 'href="other.html"' in html


def test_hr():
    assert "<hr>" in render_markdown("---")


# ---------------------------------------------------------------- 导出

def _notes():
    return {
        "alpha": {"frontmatter": {"title": "Alpha", "tags": ["work"]},
                  "body": "正文 [[beta]] 与 [[ghost]]"},
        "beta": {"frontmatter": {"tags": ["work"]},
                 "body": "回链 [[alpha]]"},
    }


def test_export_creates_structure(tmp_path):
    out = export_site(tmp_path, _notes())
    assert (out / "index.html").exists()
    assert (out / "tags.html").exists()
    assert (out / "style.css").exists()
    assert (out / "notes" / "alpha.html").exists()
    assert (out / "notes" / "beta.html").exists()


def test_export_note_page_has_backlinks(tmp_path):
    export_site(tmp_path, _notes())
    html = (tmp_path / "export" / "notes" / "alpha.html").read_text(
        encoding="utf-8")
    # alpha 被 beta 引用 → 反向链接区出现 beta
    assert "beta" in html
    # alpha 的出链有 ghost（悬空）
    assert "dangling" in html


def test_export_index_lists_all(tmp_path):
    export_site(tmp_path, _notes())
    html = (tmp_path / "export" / "index.html").read_text(encoding="utf-8")
    assert "alpha" in html and "beta" in html


def test_export_tags_page(tmp_path):
    export_site(tmp_path, _notes())
    html = (tmp_path / "export" / "tags.html").read_text(encoding="utf-8")
    assert "work" in html


def test_export_rerun_is_clean(tmp_path):
    export_site(tmp_path, _notes())
    out = export_site(tmp_path, _notes())  # 二次导出
    files = [p.name for p in (out / "notes").iterdir()]
    assert sorted(files) == ["alpha.html", "beta.html"]


def test_export_offline_no_external_refs(tmp_path):
    out = export_site(tmp_path, _notes())
    for page in out.rglob("*.html"):
        html = page.read_text(encoding="utf-8")
        assert "http://" not in html.replace("http://www.w3.org", "")
        assert "https://" not in html
        assert not re.search(r'src="https?://', html)
