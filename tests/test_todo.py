"""M21 TODO 提取测试。"""
from notesdb.todo import by_note, extract_todos, pending, progress


def _note(body):
    return {"frontmatter": None, "body": body}


# ---------------------------------------------------------------- 提取

def test_unchecked_box():
    todos = extract_todos(_note("- [ ] 买菜\n"))
    assert todos == [{"done": False, "text": "买菜", "line": 0}]


def test_checked_box_variants():
    for mark in ("x", "X"):
        todos = extract_todos(_note(f"- [{mark}] 完成\n"))
        assert todos[0]["done"] is True


def test_text_todo_kinds():
    for kind in ("TODO", "FIXME", "XXX", "todo"):
        todos = extract_todos(_note(f"- {kind}: 修这个\n"))
        assert todos[0]["text"] == "修这个"
        assert todos[0]["done"] is False


def test_line_numbers():
    todos = extract_todos(_note("引言\n- [ ] 任务\n结尾\n"))
    assert todos[0]["line"] == 1


def test_star_bullet_also_counted():
    assert extract_todos(_note("* [ ] 任务\n"))
    assert extract_todos(_note("+ [ ] 任务\n"))


def test_plain_list_item_not_todo():
    assert extract_todos(_note("- 普通列表项\n")) == []


def test_indented_checkbox():
    assert extract_todos(_note("  - [ ] 缩进任务\n"))[0]["text"] == "缩进任务"


def test_empty_body():
    assert extract_todos(_note("")) == []


# ---------------------------------------------------------------- 聚合

def _notes():
    return {
        "plan": _note("- [ ] 甲\n- [x] 乙\n- TODO: 丙\n"),
        "done-all": _note("- [x] 丁\n"),
        "no-todo": _note("普通笔记\n"),
    }


def test_by_note_only_notes_with_todos():
    assert set(by_note(_notes())) == {"plan", "done-all"}


def test_pending_excludes_done():
    pend = pending(_notes())
    texts = [t["text"] for _, t in pend]
    assert texts == ["甲", "丙"]  # 乙/丁已完成


def test_pending_sorted_by_note():
    notes = {"b": _note("- [ ] b1\n"), "a": _note("- [ ] a1\n")}
    assert [n for n, _ in pending(notes)] == ["a", "b"]


def test_progress_counts_checkboxes_only():
    p = progress(_notes())
    # checkbox：甲(未) 乙(完) 丁(完)；文字 TODO 丙不计
    assert p == {"total": 3, "done": 2, "ratio": round(2 / 3, 3)}


def test_progress_empty():
    assert progress({"a": _note("无任务\n")}) == {
        "total": 0, "done": 0, "ratio": None}
