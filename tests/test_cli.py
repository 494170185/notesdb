"""M20 CLI 端到端测试：真进程跑 python -m notesdb。

不 mock 任何层——CLI 的参数解析、退出码、输出格式
全走真实链路（subprocess 起 Python）。
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent


def cli(*args, root):
    """跑 CLI，返回 (returncode, stdout, stderr)。"""
    r = subprocess.run(
        [sys.executable, "-m", "notesdb", "--root", str(root), *args],
        capture_output=True, text=True, cwd=REPO, timeout=120,
        encoding="utf-8")
    return r.returncode, r.stdout, r.stderr


@pytest.fixture
def lib(tmp_path):
    (tmp_path / "notes").mkdir()
    (tmp_path / "notes" / "a.md").write_text(
        "---\ntitle: Alpha\ntags: [work]\n---\n内容甲 [[b]]\n", encoding="utf-8")
    (tmp_path / "notes" / "b.md").write_text(
        "内容乙 [[ghost]]\n", encoding="utf-8")
    return tmp_path


# ---------------------------------------------------------------- 只读

def test_cli_list(lib):
    code, out, _ = cli("list", root=lib)
    assert code == 0
    assert "a" in out and "work" in out


def test_cli_query(lib):
    code, out, _ = cli("query", "内容", root=lib)
    assert code == 0
    assert "命中 2/2" in out


def test_cli_query_bad_syntax(lib):
    code, _, err = cli("query", "tag:", root=lib)
    assert code == 2
    assert "语法" in err


def test_cli_stats(lib):
    code, out, _ = cli("stats", root=lib)
    assert code == 0
    assert "笔记        2" in out


def test_cli_lint(lib):
    code, out, _ = cli("lint", root=lib)
    assert code == 0  # 悬空是 warning 不是 error
    assert "ghost" in out


def test_cli_export(lib):
    code, out, _ = cli("export", root=lib)
    assert code == 0
    assert (lib / "export" / "index.html").exists()


def test_cli_report(lib):
    code, out, _ = cli("report", root=lib)
    assert code == 0
    assert "库统计报表" in out


def test_cli_walk(lib):
    code, out, _ = cli("walk", "2", "--seed", "3", root=lib)
    assert code == 0
    assert len([l for l in out.strip().splitlines() if l.strip()]) == 2


def test_cli_version():
    r = subprocess.run([sys.executable, "-m", "notesdb", "--version"],
                       capture_output=True, text=True, cwd=REPO, timeout=60,
                       encoding="utf-8")
    assert r.returncode == 0
    assert r.stdout.strip()


def test_cli_similar(lib):
    code, out, _ = cli("similar", "a", root=lib)
    assert code == 0


def test_cli_suggest(lib):
    code, out, _ = cli("suggest", "b", root=lib)
    assert code == 0
    assert "ghost" in out


def test_cli_today(lib):
    code, out, _ = cli("today", root=lib)
    assert code == 0
    assert "今日笔记" in out


# ---------------------------------------------------------------- 写入

def test_cli_new_and_list(lib):
    code, out, _ = cli("new", "fresh", "--title", "新", "--tag", "draft",
                       root=lib)
    assert code == 0
    assert (lib / "notes" / "fresh.md").exists()
    code, out, _ = cli("list", root=lib)
    assert "draft" in out


def test_cli_new_duplicate_fails(lib):
    code, _, err = cli("new", "a", root=lib)
    assert code == 2
    assert "已存在" in err


def test_cli_rename_syncs_references(lib):
    code, out, _ = cli("rename", "b", "bee", root=lib)
    assert code == 0
    assert "同步更新 1" in out
    body = (lib / "notes" / "a.md").read_text(encoding="utf-8")
    assert "[[bee]]" in body


def test_cli_delete_backs_up(lib):
    code, _, _ = cli("delete", "a", root=lib)
    assert code == 0
    assert not (lib / "notes" / "a.md").exists()
    assert list((lib / "backups").glob("backup-*.zip"))


def test_cli_tag_add_remove(lib):
    code, _, _ = cli("tag", "add", "b", "urgent", root=lib)
    assert code == 0
    body = (lib / "notes" / "b.md").read_text(encoding="utf-8")
    assert "urgent" in body
    code, _, _ = cli("tag", "remove", "b", "urgent", root=lib)
    assert code == 0
    body = (lib / "notes" / "b.md").read_text(encoding="utf-8")
    assert "urgent" not in body


def test_cli_backup_restore_cycle(lib):
    code, _, _ = cli("backup", root=lib)
    assert code == 0
    code, out, _ = cli("backups", root=lib)
    assert "backup-" in out
    zip_name = out.strip().splitlines()[0].strip()
    # 改坏库再恢复
    (lib / "notes" / "a.md").write_text("破坏", encoding="utf-8")
    code, _, _ = cli("restore", zip_name, root=lib)
    assert code == 0
    body = (lib / "notes" / "a.md").read_text(encoding="utf-8")
    assert "Alpha" in body  # 恢复到备份时刻


def test_cli_import(lib, tmp_path):
    src = lib / "incoming"
    src.mkdir()
    (src / "c.md").write_text("导入内容\n", encoding="utf-8")
    code, out, _ = cli("import", str(src), root=lib)
    assert code == 0
    assert (lib / "notes" / "c.md").exists()


def test_cli_exit_code_for_bad_command(lib):
    code, _, _ = cli("frobnicate", root=lib)
    assert code == 2
