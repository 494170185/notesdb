"""笔记库存储层（M1）：磁盘上的 notes/ 目录 ↔ 内存 dict 的读写。

口径：
- 库根目录下 notes/ 存 .md 文件，文件名（去扩展名）即笔记名；
- 名字里的非法字符（Windows 保留字符、控制字符）在 load 时
  逐文件报告而不是崩整库；
- load 返回 (notes dict, errors list)；store 单篇写回原子化
  （先写临时文件再 rename，中断不会留半截文件）。
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

from .model import parse_note

NOTES_DIRNAME = "notes"


class Store:
    """一个笔记库的磁盘视图。"""

    def __init__(self, root: str | os.PathLike):
        self.root = Path(root)
        self.notes_dir = self.root / NOTES_DIRNAME

    def load(self) -> tuple[dict[str, dict], list[str]]:
        """读全部笔记。返回 ({name: note}, errors)。"""
        notes: dict[str, dict] = {}
        errors: list[str] = []
        if not self.notes_dir.is_dir():
            return notes, errors
        for path in sorted(self.notes_dir.glob("*.md")):
            name = path.stem
            if not _valid_name(name):
                errors.append(f"非法笔记名: {name}")
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError) as e:
                errors.append(f"读取失败 {name}: {e}")
                continue
            note = parse_note(text)
            note["name"] = name
            notes[name] = note
        return notes, errors

    def store(self, name: str, note: dict) -> None:
        """写回单篇笔记。原子写：临时文件 + rename。"""
        if not _valid_name(name):
            raise ValueError(f"非法笔记名: {name!r}")
        self.notes_dir.mkdir(parents=True, exist_ok=True)
        text = render_note_of(note)
        target = self.notes_dir / f"{name}.md"
        # 同目录临时文件保证 rename 落在同一卷上
        fd, tmp = tempfile.mkstemp(dir=self.notes_dir, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
                f.write(text)
            os.replace(tmp, target)
        except BaseException:
            if os.path.exists(tmp):
                os.remove(tmp)
            raise


def render_note_of(note: dict) -> str:
    """从笔记 dict 还原文本（与 parse_note 对称）。"""
    from .model import render_note

    return render_note(note.get("frontmatter"), note.get("body", ""))


_INVALID_CHARS = set('<>:"/\\|?*')


def _valid_name(name: str) -> bool:
    """Windows 兼容的笔记名（全平台用同一口径，避免跨平台库漂移）。"""
    if not name or name.strip() != name:
        return False
    if any(c in _INVALID_CHARS or ord(c) < 32 for c in name):
        return False
    if name in {".", ".."}:
        return False
    # Windows 保留设备名（con/nul/prn/aux/com1…）
    stem = name.split(".")[0].lower()
    if stem in {"con", "prn", "aux", "nul"} or stem.startswith("com") and stem[3:].isdigit() or stem.startswith("lpt") and stem[3:].isdigit():
        return False
    return True
