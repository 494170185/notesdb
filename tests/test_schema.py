"""M32 frontmatter 架构测试。"""
import pytest

from notesdb.schema import (
    SchemaError,
    check_note,
    check_value,
    validate_schema,
)


# ---------------------------------------------------------------- schema 自检

def test_validate_schema_ok():
    validate_schema({"date": "date", "rating": "int", "status": ["a", "b"]})


def test_validate_schema_unknown_type():
    with pytest.raises(SchemaError, match="未知"):
        validate_schema({"x": "timestamp"})


def test_validate_schema_empty_enum():
    with pytest.raises(SchemaError, match="enum"):
        validate_schema({"x": []})


def test_validate_schema_non_dict():
    with pytest.raises(SchemaError):
        validate_schema(["str"])


def test_validate_schema_bad_field_name():
    with pytest.raises(SchemaError, match="字段名"):
        validate_schema({"": "str"})


# ---------------------------------------------------------------- 值检查

def test_check_value_str():
    assert check_value("f", "ok", "str") is None
    assert check_value("f", 42, "str") is not None


def test_check_value_int_rejects_bool():
    assert check_value("f", 3, "int") is None
    assert check_value("f", True, "int") is not None  # bool 不是 int


def test_check_value_bool():
    assert check_value("f", False, "bool") is None
    assert check_value("f", "yes", "bool") is not None


def test_check_value_float_accepts_int():
    assert check_value("f", 3, "float") is None
    assert check_value("f", 3.5, "float") is None
    assert check_value("f", "3.5", "float") is not None


def test_check_value_date():
    assert check_value("f", "2026-09-24", "date") is None
    assert check_value("f", "下周三", "date") is not None
    assert check_value("f", 20260924, "date") is not None


def test_check_value_enum():
    assert check_value("f", "a", ["a", "b"]) is None
    assert check_value("f", "c", ["a", "b"]) is not None


def test_check_value_none_allowed():
    assert check_value("f", None, "str") is None  # 未填不算错


def test_check_value_list():
    assert check_value("f", [1, 2], "list") is None
    assert check_value("f", "not", "list") is not None


# ---------------------------------------------------------------- 笔记检查

def test_check_note_passes():
    note = {"frontmatter": {"date": "2026-09-24", "rating": 5}}
    assert check_note(note, {"date": "date", "rating": "int"}) == []


def test_check_note_reports_errors():
    note = {"frontmatter": {"date": "昨天", "rating": "高"}}
    errors = check_note(note, {"date": "date", "rating": "int"})
    assert len(errors) == 2
    assert any(e.startswith("date") for e in errors)


def test_check_note_undeclared_fields_ignored():
    note = {"frontmatter": {"whatever": [1, 2, 3]}}
    assert check_note(note, {"date": "date"}) == []


def test_check_note_missing_field_ok():
    assert check_note({"frontmatter": {}}, {"date": "date"}) == []


def test_check_note_no_frontmatter():
    assert check_note({"frontmatter": None}, {"date": "date"}) == []
