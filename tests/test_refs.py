"""M27 外部引用检查测试。"""
from notesdb.refs import check_refs, describe_problem, extract_refs


def test_extract_image_ref():
    refs = extract_refs("看 ![图](pic.png)\n")
    assert refs == [("pic.png", 0)]


def test_extract_link_ref():
    refs = extract_refs("[文档](../docs/a.pdf)")
    assert refs == [("../docs/a.pdf", 0)]


def test_extract_skips_urls_and_anchors():
    body = "[web](https://x.com) [mail](mailto:a@b.c) [toc](#sec) ![d](data:x)"
    assert extract_refs(body) == []


def test_extract_strips_fragment_and_query():
    assert extract_refs("![x](pic.png?v=2#frag)")[0][0] == "pic.png"


def test_extract_skips_absolute_paths():
    assert extract_refs("[w](C:/x.md) [u](\\\\server\\share) [r](/root.md)") == []


def test_extract_line_numbers():
    refs = extract_refs("文本\n中间\n![图](a.png)\n")
    assert refs[0][1] == 2


def test_extract_empty():
    assert extract_refs("") == []


# ---------------------------------------------------------------- 全库核对

def _mk(root, files):
    notes_dir = root / "notes"
    notes_dir.mkdir(parents=True)
    for name, content in files.items():
        p = notes_dir / f"{name}.md"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")


def test_check_refs_reports_missing(tmp_path):
    _mk(tmp_path, {"a": "![图](ghost.png)\n", "b": "![在](pic.png)\n"})
    (tmp_path / "notes" / "pic.png").write_bytes(b"img")
    problems = check_refs(
        {"a": {"body": "![图](ghost.png)\n"},
         "b": {"body": "![在](pic.png)\n"}}, tmp_path)
    assert len(problems) == 1
    assert problems[0]["note"] == "a"
    assert problems[0]["path"] == "ghost.png"


def test_check_refs_relative_to_note_dir(tmp_path):
    """嵌套笔记的相对引用基于笔记所在目录。"""
    _mk(tmp_path, {"sub/nested": "![x](local.png)\n"})
    (tmp_path / "notes" / "sub" / "local.png").write_bytes(b"i")
    problems = check_refs(
        {"sub/nested": {"body": "![x](local.png)\n"}}, tmp_path)
    assert problems == []


def test_check_refs_parent_traversal(tmp_path):
    _mk(tmp_path, {"a": "[t](../assets/doc.pdf)\n"})
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets" / "doc.pdf").write_bytes(b"pdf")
    problems = check_refs({"a": {"body": "[t](../assets/doc.pdf)\n"}}, tmp_path)
    assert problems == []


def test_check_refs_empty_body():
    assert check_refs({"a": {"body": ""}}, "whatever") == []


def test_describe_problem():
    msg = describe_problem({"note": "a", "path": "x.png", "line": 2})
    assert "a" in msg and "x.png" in msg and "3" in msg
