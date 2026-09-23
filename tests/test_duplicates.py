"""M29 重复检测测试。"""
from notesdb.duplicates import describe_group, find_duplicates


def test_exact_duplicates_found():
    notes = {
        "a": {"body": "一样的内容\n"},
        "b": {"body": "一样的内容\n"},
        "c": {"body": "不同的\n"},
    }
    groups = find_duplicates(notes)
    assert groups == [["a", "b"]]


def test_near_duplicates_whitespace_insensitive():
    notes = {
        "a": {"body": "内容  甲\n\n内容乙\n"},
        "b": {"body": "内容 甲\n内容乙\n"},
    }
    assert find_duplicates(notes) == [["a", "b"]]


def test_no_duplicates():
    notes = {"a": {"body": "x\n"}, "b": {"body": "y\n"}}
    assert find_duplicates(notes) == []


def test_empty_bodies_not_duplicates():
    notes = {"a": {"body": ""}, "b": {"body": "   \n"}}
    assert find_duplicates(notes) == []


def test_groups_sorted_deterministically():
    notes = {
        "z1": {"body": "同\n"}, "z2": {"body": "同\n"},
        "a1": {"body": "异\n"}, "a2": {"body": "异\n"},
    }
    groups = find_duplicates(notes)
    assert [g[0] for g in groups] == ["a1", "z1"]


def test_three_way_duplicate():
    notes = {n: {"body": "同\n"} for n in "abc"}
    assert find_duplicates(notes) == [["a", "b", "c"]]


def test_empty_library():
    assert find_duplicates({}) == []


def test_describe_group():
    assert "a" in describe_group(["a", "b"])
