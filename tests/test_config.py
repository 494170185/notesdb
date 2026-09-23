"""M14 配置测试。"""
import json

import pytest

from notesdb.config import Config, ConfigError, load


def test_no_config_file_gives_defaults(tmp_path):
    cfg = load(tmp_path)
    assert cfg.index_threshold == 0.2
    assert cfg.export_dir == "export"
    assert cfg.backup_keep == 10
    assert cfg.exclude == []
    assert cfg.daily_template == ""


def test_config_file_overrides(tmp_path):
    (tmp_path / "notesdb.json").write_text(json.dumps({
        "index_threshold": 0.35,
        "backup_keep": 3,
        "exclude": ["draft-*", "private/*"],
    }), encoding="utf-8")
    cfg = load(tmp_path)
    assert cfg.index_threshold == 0.35
    assert cfg.backup_keep == 3
    assert cfg.exclude == ["draft-*", "private/*"]


def test_broken_json_raises(tmp_path):
    (tmp_path / "notesdb.json").write_text("{oops", encoding="utf-8")
    with pytest.raises(ConfigError, match="JSON"):
        load(tmp_path)


def test_unknown_key_raises(tmp_path):
    (tmp_path / "notesdb.json").write_text(
        json.dumps({"threshold": 0.5}), encoding="utf-8")
    with pytest.raises(ConfigError, match="未知配置键"):
        load(tmp_path)


def test_wrong_type_raises(tmp_path):
    (tmp_path / "notesdb.json").write_text(
        json.dumps({"backup_keep": "many"}), encoding="utf-8")
    with pytest.raises(ConfigError, match="类型"):
        load(tmp_path)


def test_threshold_out_of_range_raises(tmp_path):
    (tmp_path / "notesdb.json").write_text(
        json.dumps({"index_threshold": 1.5}), encoding="utf-8")
    with pytest.raises(ConfigError, match="index_threshold"):
        load(tmp_path)


def test_env_overrides_file(tmp_path):
    (tmp_path / "notesdb.json").write_text(
        json.dumps({"backup_keep": 5}), encoding="utf-8")
    cfg = load(tmp_path, env={"NDB_BACKUP_KEEP": "7"})
    assert cfg.backup_keep == 7


def test_env_float_and_list(tmp_path):
    cfg = load(tmp_path, env={"NDB_INDEX_THRESHOLD": "0.4",
                              "NDB_EXCLUDE": "a-*, b-*"})
    assert cfg.index_threshold == 0.4
    assert cfg.exclude == ["a-*", "b-*"]


def test_env_empty_string_ignored(tmp_path):
    cfg = load(tmp_path, env={"NDB_EXPORT_DIR": ""})
    assert cfg.export_dir == "export"


def test_top_level_not_object_raises(tmp_path):
    (tmp_path / "notesdb.json").write_text("[1, 2]", encoding="utf-8")
    with pytest.raises(ConfigError, match="顶层"):
        load(tmp_path)


def test_is_excluded_glob():
    cfg = Config(exclude=["draft-*", "private/*"])
    assert cfg.is_excluded("draft-todo")
    assert cfg.is_excluded("private/secret")
    assert not cfg.is_excluded("published")


def test_is_excluded_empty():
    assert not Config().is_excluded("anything")
