"""M45 环境自检测试。"""
from notesdb.doctor import MIN_PYTHON, doctor, run_checks


def test_all_checks_present(tmp_path):
    checks = run_checks(tmp_path)
    names = {name for _, name, _ in checks}
    assert {"python", "PyYAML", "notes 目录", "配置"} <= names


def test_healthy_environment(tmp_path):
    checks = run_checks(tmp_path)
    assert all(ok for ok, _, _ in checks)


def test_creates_missing_notes_dir(tmp_path):
    run_checks(tmp_path)
    assert (tmp_path / "notes").is_dir()


def test_bad_config_reported(tmp_path):
    (tmp_path / "notesdb.json").write_text("{broken", encoding="utf-8")
    checks = run_checks(tmp_path)
    assert any(not ok and name == "配置" for ok, name, _ in checks)


def test_doctor_exit_codes(tmp_path, capsys):
    assert doctor(tmp_path) == 0
    out = capsys.readouterr().out
    assert "环境就绪" in out

    (tmp_path / "bad").mkdir()
    (tmp_path / "bad" / "notesdb.json").write_text("{", encoding="utf-8")
    assert doctor(tmp_path / "bad") == 1


def test_min_python_sane():
    assert MIN_PYTHON[0] == 3 and MIN_PYTHON[1] >= 9
