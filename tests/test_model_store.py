"""M1 笔记模型与存储层测试。"""
import pytest

from notesdb.model import parse_note, render_note, split_frontmatter
from notesdb.store import Store


# ---------------------------------------------------------------- 模型

def test_split_with_frontmatter():
    text = "---\ntitle: Hi\ntags: [a]\n---\nbody here\n"
    fm, body = split_frontmatter(text)
    assert fm == {"title": "Hi", "tags": ["a"]}
    assert body == "body here\n"


def test_split_without_frontmatter():
    fm, body = split_frontmatter("just text\n")
    assert fm is None
    assert body == "just text\n"


def test_split_empty_frontmatter_block():
    fm, body = split_frontmatter("---\n---\nbody\n")
    assert fm == {}
    assert body == "body\n"


def test_split_broken_yaml_falls_back():
    """坏 YAML → (None, 原文)：正文还能用。"""
    text = "---\ntitle: [unclosed\n---\nbody\n"
    fm, body = split_frontmatter(text)
    assert fm is None
    assert body == text


def test_split_non_mapping_frontmatter():
    """frontmatter 是标量/列表 → 视为坏格式。"""
    fm, _ = split_frontmatter("---\njust a string\n---\nbody\n")
    assert fm is None


def test_parse_note_flags_error():
    note = parse_note("---\nbad: [\n---\nbody\n")
    assert note["frontmatter"] is None
    assert note["frontmatter_error"] is True
    assert note["body"].startswith("---")  # 原文保留


def test_parse_note_clean():
    note = parse_note("---\ntitle: T\n---\nB\n")
    assert note["frontmatter"] == {"title": "T"}
    assert note["frontmatter_error"] is False
    assert note["body"] == "B\n"


def test_render_roundtrip():
    text = "---\ntitle: Hi\n---\nbody\n"
    fm, body = split_frontmatter(text)
    assert render_note(fm, body) == text


def test_render_none_frontmatter_omits_block():
    assert render_note(None, "body\n") == "body\n"


# ---------------------------------------------------------------- 存储

def _mk_store(tmp_path):
    return Store(tmp_path)


def test_store_load_empty_dir(tmp_path):
    notes, errors = _mk_store(tmp_path).load()
    assert notes == {} and errors == []


def test_store_load_missing_dir(tmp_path):
    """notes/ 不存在 = 空库，不是错误。"""
    notes, errors = _mk_store(tmp_path / "ghost").load()
    assert notes == {} and errors == []


def test_store_roundtrip(tmp_path):
    s = _mk_store(tmp_path)
    s.store("hello", {"frontmatter": {"title": "Hello"},
                      "body": "world\n"})
    notes, errors = s.load()
    assert errors == []
    assert "hello" in notes
    assert notes["hello"]["frontmatter"] == {"title": "Hello"}
    assert notes["hello"]["body"] == "world\n"


def test_store_overwrites(tmp_path):
    s = _mk_store(tmp_path)
    s.store("a", {"frontmatter": None, "body": "v1\n"})
    s.store("a", {"frontmatter": None, "body": "v2\n"})
    notes, _ = s.load()
    assert notes["a"]["body"] == "v2\n"


def test_store_rejects_invalid_name(tmp_path):
    s = _mk_store(tmp_path)
    for bad in ("a/b", "a<b", 'a"b', "con", "", " lead", "trail "):
        with pytest.raises(ValueError):
            s.store(bad, {"frontmatter": None, "body": "x\n"})


def test_store_load_reports_invalid_files(tmp_path, monkeypatch):
    """非法名/读不了的文件：报错但不炸库、合法笔记照常读。

    Windows 文件系统写不进 `ba<d.md` 这类名字，所以非法名场景
    用 glob 结果直接注入模拟（mock glob）；读取失败场景用真实
    的「同目录下目录叫 xxx.md」触发（读目录不是文件 → OSError）。
    """
    import notesdb.store as store_mod

    s = _mk_store(tmp_path)
    (tmp_path / "notes").mkdir()
    (tmp_path / "notes" / "good.md").write_text("ok\n", encoding="utf-8")
    (tmp_path / "notes" / "adir.md").mkdir()  # glob 会命中但 read_text 失败

    # 注入一个「磁盘上不该出现」的非法名（绕过文件系统直接给 glob 结果）
    from pathlib import Path

    real_glob = Path.glob

    def fake_glob(self, pattern):
        for p in real_glob(self, pattern):
            yield p
        if self.name == "notes" and pattern == "*.md":
            yield Path(str(self) + "\\") / "ba<d.md"

    monkeypatch.setattr(Path, "glob", fake_glob)

    notes, errors = s.load()
    assert "good" in notes
    assert any("ba<d" in e for e in errors)
    assert any("adir" in e for e in errors)


def test_store_atomic_no_tmp_leftover(tmp_path):
    """写入后目录里没有 .tmp 残留。"""
    s = _mk_store(tmp_path)
    s.store("a", {"frontmatter": None, "body": "x\n"})
    leftovers = [p.name for p in (tmp_path / "notes").iterdir()
                 if p.name.endswith(".tmp")]
    assert leftovers == []
