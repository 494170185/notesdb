"""M23 缓存与变更检测测试。"""
import os
import time

from notesdb.cache import LibraryCache, scan_changes


def _mk(root, files):
    notes = root / "notes"
    notes.mkdir(parents=True, exist_ok=True)
    for name, content in files.items():
        p = notes / f"{name}.md"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")


def test_cache_first_load(tmp_path):
    _mk(tmp_path, {"a": "x\n"})
    cache = LibraryCache(tmp_path)
    notes, errors = cache.load()
    assert "a" in notes and errors == []


def test_cache_returns_same_object_when_unchanged(tmp_path):
    """指纹不变时直接给缓存（同一 dict 对象）。"""
    _mk(tmp_path, {"a": "x\n"})
    cache = LibraryCache(tmp_path)
    n1, _ = cache.load()
    n2, _ = cache.load()
    assert n1 is n2


def test_cache_reloads_after_change(tmp_path):
    _mk(tmp_path, {"a": "1\n"})
    cache = LibraryCache(tmp_path)
    n1, _ = cache.load()
    # 确保文件名里的 mtime 与上次不同（有些文件系统精度低）
    (tmp_path / "notes" / "a.md").write_text("2\n", encoding="utf-8")
    # touch 一下保 mtime 变化
    os_path = tmp_path / "notes" / "a.md"
    st = os_path.stat()
    os.utime(os_path, (st.st_atime, st.st_mtime + 10))
    n2, _ = cache.load()
    assert n2 is not n1
    assert n2["a"]["body"] == "2\n"


def test_cache_reloads_after_new_file(tmp_path):
    _mk(tmp_path, {"a": "1\n"})
    cache = LibraryCache(tmp_path)
    cache.load()
    _mk(tmp_path, {"b": "2\n"})
    n2, _ = cache.load()
    assert "b" in n2


def test_cache_invalidate_forces_reload(tmp_path):
    _mk(tmp_path, {"a": "1\n"})
    cache = LibraryCache(tmp_path)
    n1, _ = cache.load()
    cache.invalidate()
    n2, _ = cache.load()
    assert n1 is not n2


def test_cache_empty_library(tmp_path):
    cache = LibraryCache(tmp_path)
    notes, errors = cache.load()
    assert notes == {} and errors == []


def test_fingerprint_changes_on_content(tmp_path):
    _mk(tmp_path, {"a": "1\n"})
    cache = LibraryCache(tmp_path)
    fp1 = cache.fingerprint()
    _mk(tmp_path, {"b": "2\n"})
    assert cache.fingerprint() != fp1


# ---------------------------------------------------------------- 增量扫描

def test_scan_changes_all_kinds(tmp_path):
    _mk(tmp_path, {"a": "1\n", "b": "2\n", "c": "3\n"})
    # 第一次扫描建立基线
    store = scan_changes(tmp_path, {})
    assert set(store["added"]) == {"a", "b", "c"}

    # 用 load 建 mtime 表
    current = _mtimes(tmp_path)
    _mk(tmp_path, {"d": "4\n"})                       # 新增
    (tmp_path / "notes" / "a.md").unlink()            # 删除
    time.sleep(0.01)
    p = tmp_path / "notes" / "b.md"
    p.write_text("modified\n", encoding="utf-8")      # 修改
    st = p.stat()
    os.utime(p, (st.st_atime, st.st_mtime + 5))

    changes = scan_changes(tmp_path, current)
    assert changes["added"] == ["d"]
    assert changes["removed"] == ["a"]
    assert changes["modified"] == ["b"]


def test_scan_changes_no_changes(tmp_path):
    _mk(tmp_path, {"a": "1\n"})
    current = _mtimes(tmp_path)
    assert scan_changes(tmp_path, current) == {
        "added": [], "modified": [], "removed": []}


def _mtimes(root):
    from notesdb.store import Store
    store = Store(root)
    notes, _ = store.load()
    return {n: store.path_of(n).stat().st_mtime for n in notes}
