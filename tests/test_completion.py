"""M36 shell 补全测试。"""
from notesdb.__main__ import build_parser
from notesdb.completion import bash_script, write_scripts, zsh_script


def test_bash_script_lists_all_subcommands():
    script = bash_script(build_parser())
    cmds = {"list", "query", "new", "rename", "export", "lint", "walk"}
    for c in cmds:
        assert c in script
    assert "complete -F" in script


def test_zsh_script_structure():
    script = zsh_script(build_parser())
    assert script.startswith("#compdef notesdb")
    assert "_describe" in script


def test_bash_script_generated_from_parser():
    """补全来自 argparse（新增命令自动出现）。"""
    script = bash_script(build_parser())
    assert "suggest" in script and "inbox" not in script  # 当前命令集


def test_write_scripts_creates_both(tmp_path):
    paths = write_scripts(build_parser(), str(tmp_path))
    assert len(paths) == 2
    for p in paths:
        with open(p, encoding="utf-8") as f:
            assert f.read().strip()
