"""M26 别名测试。"""
from notesdb.alias import all_names, note_aliases, resolve_name


def _note(aliases=None, **fm):
    front = dict(fm)
    if aliases is not None:
        front["aliases"] = aliases
    return {"frontmatter": front, "body": ""}


def test_aliases_from_list():
    assert note_aliases(_note(["A", "B"])) == ["A", "B"]


def test_aliases_dedupe_and_strip():
    assert note_aliases(_note([" A ", "A", "B"])) == ["A", "B"]


def test_aliases_skip_empty_and_non_string():
    assert note_aliases(_note(["", " ", 42, "ok"])) == ["ok"]


def test_aliases_missing():
    assert note_aliases({"frontmatter": None, "body": ""}) == []


def test_aliases_non_list_ignored():
    assert note_aliases(_note("单字符串")) == []


def test_resolve_name_direct():
    notes = {"real": _note()}
    assert resolve_name("real", notes) == "real"


def test_resolve_name_via_alias():
    notes = {"real": _note(aliases=["俗称"])}
    assert resolve_name("俗称", notes) == "real"


def test_resolve_name_dangling():
    assert resolve_name("ghost", {"real": _note()}) is None


def test_all_names_maps_aliases():
    notes = {
        "a": _note(aliases=["甲"]),
        "b": _note(aliases=["乙", "bee"]),
    }
    mapping = all_names(notes)
    assert mapping["a"] == "a" and mapping["甲"] == "a"
    assert mapping["b"] == "b" and mapping["乙"] == "b" and mapping["bee"] == "b"


def test_all_names_real_name_wins_conflict():
    """别名撞别家本名：本名优先。"""
    notes = {
        "a": _note(aliases=["b"]),  # a 的别名撞 b 的本名
        "b": _note(),
    }
    mapping = all_names(notes)
    assert mapping["b"] == "b"  # 本名不被别名覆盖
