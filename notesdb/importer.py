"""批量导入（M17）：把外部 Markdown 目录导入笔记库。

场景：从 Obsidian/Typora/散落的 .txt 迁移过来。规则：

  import_dir(src, root, mode)
    src 里的 .md 文件逐个导入（重读为笔记保证格式规范）；
    非 .md 的 .txt 也收（当无 frontmatter 笔记）。

  命名冲突三策略（mode）：
    skip     跳过，报告冲突（默认——安全）
    suffix   自动加后缀 -imported、-imported-2 …
    overwrite 覆盖（导入前自动备份，与 delete 同一安全网）

  子目录结构保留在笔记名里："sub/page.md" → 笔记名 "sub/page"。
  笔记名含非法字符（Windows 保留字）的文件跳过并报告。

返回 ImportResult（created/skipped/renamed/errors 明细），
CLI 拿去打印。损坏文件（编码/读取失败）不中断整批导入。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .model import parse_note
from .store import Store, _valid_name


@dataclass
class ImportResult:
    created: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)     # 冲突跳过
    renamed: list[tuple[str, str]] = field(default_factory=list)  # (原名, 新名)
    errors: list[str] = field(default_factory=list)

    def summary(self) -> str:
        return (f"导入 {len(self.created)}（重命名 {len(self.renamed)}，"
                f"跳过 {len(self.skipped)}，失败 {len(self.errors)}）")


def import_dir(src: str | Path, root: str | Path,
               mode: str = "skip") -> ImportResult:
    """把 src 目录的 Markdown/txt 导入 root 笔记库。"""
    if mode not in ("skip", "suffix", "overwrite"):
        raise ValueError(f"mode 只支持 skip/suffix/overwrite，收到 {mode!r}")
    src = Path(src)
    if not src.is_dir():
        raise FileNotFoundError(f"导入源不是目录: {src}")

    store = Store(root)
    notes, _ = store.load()
    existing: set[str] = set(notes)
    result = ImportResult()

    for path in sorted(src.rglob("*")):
        if path.suffix.lower() not in (".md", ".txt"):
            continue
        rel = path.relative_to(src).with_suffix("")
        name = rel.as_posix()  # 子目录结构进入笔记名
        if not _valid_name(name):
            result.errors.append(f"非法笔记名: {name}")
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as e:
            result.errors.append(f"读取失败 {name}: {e}")
            continue
        note = parse_note(text)

        if name in existing:
            if mode == "skip":
                result.skipped.append(name)
                continue
            if mode == "overwrite":
                from .backup import backup
                backup(root)  # 覆盖前备份一次（同 delete 的安全网）
                store.store(name, note)
                result.created.append(name)
                continue
            # suffix 模式：找可用后缀名
            new_name = _suffix_name(name, existing)
            result.renamed.append((name, new_name))
            name = new_name

        store.store(name, note)
        result.created.append(name)
        existing.add(name)

    return result


def _suffix_name(name: str, existing: set[str]) -> str:
    """name 被占用时生成 name-imported / name-imported-2 …"""
    candidate = f"{name}-imported"
    k = 2
    while candidate in existing:
        candidate = f"{name}-imported-{k}"
        k += 1
    return candidate
