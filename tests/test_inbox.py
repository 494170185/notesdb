"""M35 收件箱测试。"""
import pytest

from notesdb.inbox import INBOX_NAME, append, clear, read


def test_append_creates_inbox_note(tmp_path):
    append(tmp_path, "第一个闪念")
    assert (tmp_path / "notes" / "inbox.md").exists()
    entries = read(tmp_path)
    assert len(entries) == 1
    assert entries[0]["text"] == "第一个闪念"


def test_append_accumulates(tmp_path):
    append(tmp_path, "一")
    append(tmp_path, "二")
    entries = read(tmp_path)
    assert [e["text"] for e in entries] == ["一", "二"]


def test_append_multiline_text(tmp_path):
    append(tmp_path, "第一行\n第二行")
    entries = read(tmp_path)
    assert "第二行" in entries[0]["text"]


def test_inbox_is_regular_note(tmp_path):
    """inbox.md 有 frontmatter（可查询/导出的普通笔记）。"""
    append(tmp_path, "x")
    from notesdb.store import Store

    notes, _ = Store(tmp_path).load()
    assert INBOX_NAME in notes
    assert notes[INBOX_NAME]["frontmatter"]["tags"] == ["inbox"]


def test_append_empty_raises(tmp_path):
    with pytest.raises(ValueError, match="不能为空"):
        append(tmp_path, "   ")


def test_read_empty_library(tmp_path):
    assert read(tmp_path) == []


def test_clear_returns_count_and_empties(tmp_path):
    append(tmp_path, "一")
    append(tmp_path, "二")
    assert clear(tmp_path) == 2
    assert read(tmp_path) == []
    assert not (tmp_path / "notes" / "inbox.md").exists()


def test_clear_empty_noop(tmp_path):
    assert clear(tmp_path) == 0
