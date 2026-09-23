"""Shell 补全（M36）：给 notesdb 生成 bash/zsh 补全脚本。

手工写补全脚本易过期（命令一加就忘了同步）。这里从
argparse 的真实定义生成——parser 是单一事实源，补全
永远和 CLI 同步。

  bash_script(parser)    bash 补全（complete -W 词表方案）
  zsh_script(parser)     zsh compdef 脚本

词表方案（不含参数级补全）：对笔记工具够用——
子命令名 + 常用文件名场景由 shell 自身处理。
"""
from __future__ import annotations


def _subcommands(parser) -> list[str]:
    action = parser._subparsers._group_actions[0]  # noqa: SLF001
    return sorted(action.choices)


def bash_script(parser, prog: str = "notesdb") -> str:
    """bash 补全：第一个词补子命令。"""
    cmds = " ".join(_subcommands(parser))
    return f"""\
# notesdb bash completion（由 argparse 定义生成，勿手改）
_{prog}_completions() {{
    local cur="${{COMP_WORDS[COMP_CWORD]}}"
    if [ "$COMP_CWORD" -eq 1 ]; then
        COMPREPLY=( $(compgen -W "{cmds}" -- "$cur") )
    fi
}}
complete -F _{prog}_completions {prog}
"""


def zsh_script(parser, prog: str = "notesdb") -> str:
    """zsh 补全：compdef + 子命令词表。"""
    cmds = " ".join(_subcommands(parser))
    return f"""\
#compdef {prog}
# notesdb zsh completion（由 argparse 定义生成，勿手改）
_{prog}() {{
    local -a subcmds
    subcmds=({cmds})
    if (( CURRENT == 2 )); then
        _describe 'command' subcmds
    else
        _files
    fi
}}
_{prog} "$@"
"""


def write_scripts(parser, out_dir, prog: str = "notesdb") -> list[str]:
    """落盘 bash/zsh 两个补全脚本。返回路径列表。"""
    import os

    paths = []
    for name, content in (
        (f"{prog}-completion.bash", bash_script(parser, prog)),
        (f"_{prog}", zsh_script(parser, prog)),
    ):
        path = os.path.join(out_dir, name)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
        paths.append(path)
    return paths
