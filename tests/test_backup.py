"""M9 备份测试。"""
import zipfile

import pytest

from notesdb.backup import backup, list_backups, restore


def _seed(root, files):
    notes = root / "notes"
    notes.mkdir(parents=True)
    for name, content in files.items():
        target = notes / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    return notes


def test_backup_creates_zip(tmp_path):
    _seed(tmp_path, {"a.md": "A", "b.md": "B"})
    path = backup(tmp_path)
    assert path.exists()
    assert path.name.startswith("backup-")
    with zipfile.ZipFile(path) as zf:
        assert sorted(zf.namelist()) == ["a.md", "b.md"]


def test_backup_keeps_subdirs(tmp_path):
    _seed(tmp_path, {"sub/c.md": "C", "a.md": "A"})
    with zipfile.ZipFile(backup(tmp_path)) as zf:
        assert "sub/c.md" in zf.namelist()


def test_backup_no_notes_dir_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        backup(tmp_path)


def test_backup_prune_oldest(tmp_path):
    _seed(tmp_path, {"a.md": "A"})
    for _ in range(12):
        backup(tmp_path, keep=5)
    backups = list_backups(tmp_path)
    assert len(backups) == 5
    # 名字升序=时间序，最老的 7 个被删
    assert all(b.exists() for b in backups)


def test_backup_keep_zero_disables_prune(tmp_path):
    _seed(tmp_path, {"a.md": "A"})
    for _ in range(3):
        backup(tmp_path, keep=0)
    assert len(list_backups(tmp_path)) == 3


def test_list_backups_sorted_ascending(tmp_path):
    _seed(tmp_path, {"a.md": "A"})
    backup(tmp_path)
    backup(tmp_path)
    names = [b.name for b in list_backups(tmp_path)]
    assert names == sorted(names)


def test_same_second_backups_unique_names(tmp_path):
    """同秒多次备份文件名不撞（进程内序号）。"""
    _seed(tmp_path, {"a.md": "A"})
    p1 = backup(tmp_path)
    p2 = backup(tmp_path)
    assert p1 != p2


def test_restore_recovers_files(tmp_path):
    _seed(tmp_path, {"a.md": "v1"})
    path = backup(tmp_path)
    # 改坏库
    (tmp_path / "notes" / "a.md").write_text("v2 被误删内容", encoding="utf-8")
    (tmp_path / "notes" / "b.md").write_text("新加的", encoding="utf-8")
    count = restore(tmp_path, path)
    assert count == 1
    assert (tmp_path / "notes" / "a.md").read_text(encoding="utf-8") == "v1"
    assert not (tmp_path / "notes" / "b.md").exists()  # 恢复=回到那一刻


def test_restore_preserves_old_dir_as_broken(tmp_path):
    """恢复前旧 notes/ 改名保留，不直接删（退路）。"""
    _seed(tmp_path, {"a.md": "v1"})
    path = backup(tmp_path)
    (tmp_path / "notes" / "a.md").write_text("v2", encoding="utf-8")
    restore(tmp_path, path)
    broken = [p for p in tmp_path.iterdir() if p.name.startswith("notes.broken-")]
    assert len(broken) == 1
    assert (broken[0] / "a.md").read_text(encoding="utf-8") == "v2"


def test_restore_missing_backup_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        restore(tmp_path, tmp_path / "ghost.zip")


def test_restore_blocks_zip_slip(tmp_path):
    """zip 里的恶意成员名（../evil.md）不能写到 notes/ 外。"""
    _seed(tmp_path, {"a.md": "A"})
    evil = tmp_path / "evil.zip"
    with zipfile.ZipFile(evil, "w") as zf:
        zf.writestr("../escaped.md", "boom")
        zf.writestr("ok.md", "fine")
    count = restore(tmp_path, evil)
    assert count == 1  # 只有 ok.md
    assert not (tmp_path / "escaped.md").exists()
