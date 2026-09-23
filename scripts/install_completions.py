"""安装 shell 补全脚本（M46 配套工具）。

把生成的 bash/zsh 补全装到用户环境：
  bash → ~/.local/share/bash-completion/completions/（Linux）
         或 Git Bash 的 ~/bash_completion.d/（Windows）
  zsh  → 用户 fpath 早期目录 ~/zfunc（不存在则建）

用法:
    python scripts/install_completions.py           # 双 shell 都装
    python scripts/install_completions.py bash      # 只装 bash
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from notesdb.__main__ import build_parser  # noqa: E402
from notesdb.completion import write_scripts  # noqa: E402


def install_dir(shell: str) -> str:
    """补全脚本的目标目录（按平台惯例）。"""
    home = os.path.expanduser("~")
    if shell == "bash":
        if os.name == "nt":
            # Git Bash：~/bash_completion.d
            d = os.path.join(home, "bash_completion.d")
        else:
            d = os.path.join(home, ".local", "share",
                             "bash-completion", "completions")
    else:
        d = os.path.join(home, "zfunc")
    os.makedirs(d, exist_ok=True)
    return d


def main() -> int:
    shells = sys.argv[1:] or ["bash", "zsh"]
    for s in shells:
        if s not in ("bash", "zsh"):
            print(f"未知 shell: {s}（支持 bash/zsh）", file=sys.stderr)
            return 2
    for s in shells:
        out_dir = install_dir(s)
        paths = write_scripts(build_parser(), out_dir)
        for p in paths:
            print(f"已安装: {p}")
    print("重新打开终端后生效")
    return 0


if __name__ == "__main__":
    sys.exit(main())
