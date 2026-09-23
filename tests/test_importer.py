"""M17 批量导入测试。"""
import pytest

from notesdb.importer import import_dir
from notesdb.store import Store


@pytest.fixture
def src(tmp_path):
    d = tmp_path / "incoming"
    (d / "sub").mkdir(parents=True)
    (d / "a.md").write_text("---\ntitle: A\n---\n内容甲\n", encoding="utf-8")
    (d / "sub" / "b.md").write_text("内容乙\n", encoding="utf-8")
    (d / "c.txt").write_text("纯文本也收\n", encoding="utf-8")
    (d / "ignored.bin").write_bytes(b"\x00\x01")
    return d


@pytest.fixture
def lib(tmp_path):
    (tmp_path / "notes").mkdir()
    return tmp_path


def _names(root):
    return set(Store(root).load()[0])


def test_import_creates_notes(src, lib):
    r = import_dir(src, lib)
    assert "a" in r.created
    assert "sub/b" in r.created      # 子目录保留在名里
    assert "c" in r.created          # txt 也导入
    assert _names(lib) == {"a", "sub/b", "c"}


def test_import_preserves_frontmatter(src, lib):
    import_dir(src, lib)
    notes = Store(lib).load()[0]
    assert notes["a"]["frontmatter"] == {"title": "A"}
    assert notes["sub/b"]["frontmatter"] is None


def test_import_skip_mode(src, lib):
    (lib / "notes" / "a.md").write_text("已有\n", encoding="utf-8")
    r = import_dir(src, lib, mode="skip")
    assert r.skipped == ["a"]
    assert "a" not in r.created
    assert (lib / "notes" / "a.md").read_text(encoding="utf-8") == "已有\n"


def test_import_suffix_mode(src, lib):
    (lib / "notes" / "a.md").write_text("已有\n", encoding="utf-8")
    r = import_dir(src, lib, mode="suffix")
    assert r.renamed == [("a", "a-imported")]
    assert "a-imported" in _names(lib)
    # 原笔记未动
    assert (lib / "notes" / "a.md").read_text(encoding="utf-8") == "已有\n"


def test_import_suffix_increments(src, lib):
    (lib / "notes" / "a.md").write_text("1\n", encoding="utf-8")
    (lib / "notes" / "a-imported.md").write_text("2\n", encoding="utf-8")
    r = import_dir(src, lib, mode="suffix")
    assert r.renamed == [("a", "a-imported-2")]


def test_import_overwrite_mode_backs_up(src, lib):
    (lib / "notes" / "a.md").write_text("旧\n", encoding="utf-8")
    r = import_dir(src, lib, mode="overwrite")
    assert "a" in r.created
    notes = Store(lib).load()[0]
    assert notes["a"]["body"] == "内容甲\n"
    assert list((lib / "backups").glob("backup-*.zip"))  # 覆盖前备份


def test_import_reports_bad_name(src, lib):
    # 注入一个 glob 得到但名字非法的项：直接在 store 层面不好造，
    # 用 monkeypatch 模拟 _valid_name 拒绝 sub/b
    import notesdb.importer as imp

    orig = imp._valid_name
    imp._valid_name = lambda n: False if n == "sub/b" else orig(n)
    try:
        r = import_dir(src, lib)
    finally:
        imp._valid_name = orig
    assert any("sub/b" in e for e in r.errors)


def test_import_missing_source_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        import_dir(tmp_path / "ghost", tmp_path)


def test_import_bad_mode_raises(src, lib):
    with pytest.raises(ValueError, match="mode"):
        import_dir(src, lib, mode="merge")


def test_import_result_summary(src, lib):
    r = import_dir(src, lib)
    s = r.summary()
    assert "导入 3" in s


def test_import_continues_after_bad_file(src, lib):
    bad = src / "bad.md"
    bad.write_bytes(b"\xff\xfe\x00bad")  # 非 UTF-8
    r = import_dir(src, lib)
    assert any("bad" in e for e in r.errors)
    assert "a" in r.created  # 坏文件不中断整批
