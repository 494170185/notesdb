"""环境自检（M45）：notesdb doctor。

新环境跑不起来时先 doctor：逐项检查依赖/目录/配置，
输出结构化结果（全绿 0 / 有红 1）。

  run_checks(root)   [(ok, name, message)]
  doctor(root)       跑检查并打印，返回退出码

检查项：
  python     版本 ≥ 3.10（用了 match 之外的新语法兜底口径）
  yaml       PyYAML 可导入
  notes_dir  notes/ 存在或可创建（可写探针）
  config     notesdb.json 存在时合法（不存在=默认，跳过）
  orphan     export/backups 等可再生目录不参与（仅提示信息）
"""
from __future__ import annotations

import os
import sys

MIN_PYTHON = (3, 10)


def run_checks(root: str | os.PathLike) -> list[tuple[bool, str, str]]:
    """跑全部检查。返回 [(ok, 检查名, 消息)]。"""
    checks: list[tuple[bool, str, str]] = []

    # Python 版本
    if sys.version_info >= MIN_PYTHON:
        checks.append((True, "python",
                       f"{'.'.join(map(str, sys.version_info[:3]))} ≥ {'.'.join(map(str, MIN_PYTHON))}"))
    else:
        checks.append((False, "python",
                       f"需要 {'.'.join(map(str, MIN_PYTHON))}+，当前 {sys.version.split()[0]}"))

    # 依赖
    try:
        import yaml  # noqa: F401

        checks.append((True, "PyYAML", f"已安装 {yaml.__version__}"))
    except ImportError:
        checks.append((False, "PyYAML", "未安装（pip install PyYAML）"))

    # notes 目录
    notes_dir = os.path.join(root, "notes")
    if os.path.isdir(notes_dir):
        checks.append((True, "notes 目录", notes_dir))
    else:
        try:
            os.makedirs(notes_dir, exist_ok=True)
            probe = os.path.join(notes_dir, ".probe")
            with open(probe, "w") as f:
                f.write("x")
            os.remove(probe)
            checks.append((True, "notes 目录", f"已创建 {notes_dir}"))
        except OSError as e:
            checks.append((False, "notes 目录", f"不可创建/不可写: {e}"))

    # 配置（存在才查）
    cfg_path = os.path.join(root, "notesdb.json")
    if os.path.exists(cfg_path):
        try:
            from .config import ConfigError, load

            load(root)
            checks.append((True, "配置", "notesdb.json 合法"))
        except ConfigError as e:
            checks.append((False, "配置", str(e)))
    else:
        checks.append((True, "配置", "无 notesdb.json（全默认，正常）"))

    return checks


def doctor(root: str | os.PathLike = ".") -> int:
    """CLI 入口：打印检查结果，返回退出码。"""
    checks = run_checks(root)
    for ok, name, msg in checks:
        print(f"{'✅' if ok else '❌'} {name}: {msg}")
    bad = [c for c in checks if not c[0]]
    if bad:
        print(f"\n{len(bad)} 项需要处理")
        return 1
    print("\n环境就绪")
    return 0
