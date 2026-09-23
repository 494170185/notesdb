"""M43 JSON 交换测试。"""
import json

import pytest

from notesdb.exchange import FORMAT_VERSION, export_json, import_json


def _notes():
    return {
        "b": {"frontmatter": None, "body": "乙\n"},
        "a": {"frontmatter": {"title": "甲"}, "body": "甲内容\n"},
    }


def test_export_structure():
    payload = json.loads(export_json(_notes()))
    assert payload["version"] == FORMAT_VERSION
    assert "exported_at" in payload
    names = [n["name"] for n in payload["notes"]]
    assert names == ["a", "b"]  # 排序稳定


def test_export_roundtrip():
    text = export_json(_notes())
    merged = import_json(text, {})
    assert merged["a"]["frontmatter"] == {"title": "甲"}
    assert merged["b"]["body"] == "乙\n"


def test_import_into_existing_skip():
    text = export_json({"a": {"frontmatter": None, "body": "新\n"}})
    merged = import_json(text, {"a": {"frontmatter": None, "body": "旧\n"}})
    assert merged["a"]["body"] == "旧\n"


def test_import_into_existing_overwrite():
    text = export_json({"a": {"frontmatter": None, "body": "新\n"}})
    merged = import_json(text, {"a": {"frontmatter": None, "body": "旧\n"}},
                         mode="overwrite")
    assert merged["a"]["body"] == "新\n"


def test_import_into_existing_suffix():
    text = export_json({"a": {"frontmatter": None, "body": "新\n"}})
    merged = import_json(text, {"a": {"frontmatter": None, "body": "旧\n"}},
                         mode="suffix")
    assert merged["a"]["body"] == "旧\n"
    assert merged["a-imported"]["body"] == "新\n"


def test_import_does_not_mutate_existing():
    existing = {"a": {"frontmatter": None, "body": "旧\n"}}
    text = export_json({"a": {"frontmatter": None, "body": "新\n"}})
    import_json(text, existing)
    assert existing["a"]["body"] == "旧\n"


def test_import_bad_json_raises():
    with pytest.raises(ValueError, match="JSON"):
        import_json("{broken", {})


def test_import_bad_structure_raises():
    with pytest.raises(ValueError, match="结构"):
        import_json(json.dumps({"data": []}), {})


def test_import_future_version_raises():
    payload = {"version": 99, "notes": []}
    with pytest.raises(ValueError, match="版本"):
        import_json(json.dumps(payload), {})


def test_import_skips_nameless():
    payload = {"version": 1, "notes": [{"body": "x"}, {"name": "ok", "body": "y"}]}
    merged = import_json(json.dumps(payload), {})
    assert set(merged) == {"ok"}


def test_import_bad_mode():
    with pytest.raises(ValueError, match="mode"):
        import_json(export_json({}), {}, mode="merge")
