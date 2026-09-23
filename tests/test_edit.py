"""M10 编辑操作测试。"""
import pytest

from notesdb.edit import EditError, add_tag, delete, new, remove_tag, rename
from notesdb.store import Store


@pytest.fixture
def lib(tmp_path):
    (tmp_path / "notes").mkdir()
    (tmp_path / "notes" / "alpha.md").write_text(
        "---\ntitle: A\ntags: [work]\n---\n内容见 [[beta]]\n", encoding="utf-8")
    (tmp_path / "notes" / "beta.md").write_text(
        "回看 [[alpha]] 和 [[gamma]]\n", encoding="utf-8")
    return tmp_path


def _load(root):
    return Store(root).load()[0]


# ---------------------------------------------------------------- new

def test_new_creates_note(lib):
    new(lib, "fresh", title="新笔记", tags=["draft"])
    notes = _load(lib)
    assert "fresh" in notes
    assert notes["fresh"]["frontmatter"]["title"] == "新笔记"
    assert notes["fresh"]["frontmatter"]["tags"] == ["draft"]


def test_new_duplicate_raises(lib):
    with pytest.raises(EditError, match="已存在"):
        new(lib, "alpha")


def test_new_without_frontmatter(lib):
    new(lib, "plain", body="只有正文")
    notes = _load(lib)
    assert notes["plain"]["frontmatter"] is None
    assert notes["plain"]["body"] == "只有正文"


# ---------------------------------------------------------------- rename

def test_rename_moves_note_and_updates_references(lib):
    updated = rename(lib, "beta", "beta-v2")
    notes = _load(lib)
    assert "beta-v2" in notes and "beta" not in notes
    # alpha 里的 [[beta]] 同步更新
    assert "[[beta-v2]]" in notes["alpha"]["body"]
    assert updated == 1


def test_rename_updates_all_referencing_notes(lib):
    (lib / "notes" / "third.md").write_text("也引用 [[beta]]\n", encoding="utf-8")
    updated = rename(lib, "beta", "beta-v2")
    notes = _load(lib)
    assert "[[beta-v2]]" in notes["third"]["body"]
    assert updated == 2


def test_rename_keeps_alias_part(lib):
    (lib / "notes" / "alias.md").write_text(
        "[[beta|别名]] 引用\n", encoding="utf-8")
    rename(lib, "beta", "beta-v2")
    notes = _load(lib)
    assert "[[beta-v2|别名]]" in notes["alias"]["body"]


def test_rename_dangling_reference_untouched(lib):
    """引用 gamma（本来就不存在）不受 beta 改名影响。"""
    rename(lib, "beta", "beta-v2")
    notes = _load(lib)
    assert "[[gamma]]" in notes["beta-v2"]["body"]


def test_rename_self_reference(lib):
    (lib / "notes" / "beta.md").write_text(
        "自引用 [[beta]]\n", encoding="utf-8")
    rename(lib, "beta", "beta-v2")
    notes = _load(lib)
    assert "beta" not in notes
    assert "[[beta-v2]]" in notes["beta-v2"]["body"]


def test_rename_missing_raises(lib):
    with pytest.raises(EditError, match="不存在"):
        rename(lib, "ghost", "x")


def test_rename_to_existing_name_raises(lib):
    with pytest.raises(EditError, match="已存在"):
        rename(lib, "beta", "alpha")


# ---------------------------------------------------------------- tags

def test_add_tag(lib):
    add_tag(lib, "beta", "Reading")
    notes = _load(lib)
    assert "reading" in notes["beta"]["frontmatter"]["tags"]


def test_add_tag_creates_tags_field(lib):
    add_tag(lib, "beta", "new-tag")
    assert "new-tag" in _load(lib)["beta"]["frontmatter"]["tags"]


def test_add_tag_idempotent(lib):
    add_tag(lib, "alpha", "WORK")  # 大小写归一到已有 work
    tags = _load(lib)["alpha"]["frontmatter"]["tags"]
    assert tags.count("work") == 1


def test_remove_tag(lib):
    remove_tag(lib, "alpha", "work")
    assert "tags" not in _load(lib)["alpha"]["frontmatter"]


def test_remove_last_tag_removes_field(lib):
    remove_tag(lib, "alpha", "work")
    # frontmatter 还有 title，保留
    assert _load(lib)["alpha"]["frontmatter"]["title"] == "A"


def test_remove_missing_tag_raises(lib):
    with pytest.raises(EditError, match="没有标签"):
        remove_tag(lib, "alpha", "ghost-tag")


# ---------------------------------------------------------------- delete

def test_delete_removes_note_and_backs_up(lib):
    delete(lib, "alpha")
    assert "alpha" not in _load(lib)
    backups = list((lib / "backups").glob("backup-*.zip"))
    assert len(backups) == 1  # 删除前自动备份


def test_delete_without_backup(lib):
    delete(lib, "alpha", backup_first=False)
    assert "alpha" not in _load(lib)
    assert not (lib / "backups").exists()


def test_delete_missing_raises(lib):
    with pytest.raises(EditError):
        delete(lib, "ghost")
