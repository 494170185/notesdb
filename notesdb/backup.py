"""备份与快照（M9）：把 notes/ 打包成带时间戳的 zip。

口径：
- 备份内容 = notes/ 目录全量（笔记是全部有价值数据；
  export/ 可再生、索引在内存）；
- 文件名 backup-YYYYMMDD-HHMMSS.zip（秒级时间戳 + 进程内
  单调序号防同秒撞名——教训来自别的项目的三个字典序 bug）；
- 保留策略：默认 keep=10，超出的最老备份删除；
- 恢复：restore() 把备份解压回 notes/（先清空目标——
  备份恢复的语义就是"回到那一刻"，不是合并）。
"""
from __future__ import annotations

import shutil
import zipfile
from datetime import datetime
from pathlib import Path

BACKUP_DIRNAME = "backups"
BACKUP_PREFIX = "backup-"

# 进程内单调计数器：同一秒内多次备份不撞名
_sequence = 0


def backup(root: str | Path, keep: int = 10) -> Path:
    """打包 notes/ 为 backups/backup-<ts>.zip。返回备份文件路径。"""
    global _sequence
    root = Path(root)
    notes_dir = root / "notes"
    if not notes_dir.is_dir():
        raise FileNotFoundError(f"没有可备份的笔记目录: {notes_dir}")

    backup_dir = root / BACKUP_DIRNAME
    backup_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    _sequence += 1
    path = backup_dir / f"{BACKUP_PREFIX}{ts}-{_sequence:02d}.zip"

    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        for md in sorted(notes_dir.rglob("*")):
            if md.is_file():
                zf.write(md, md.relative_to(notes_dir))

    if keep > 0:
        _prune(backup_dir, keep)
    return path


def _prune(backup_dir: Path, keep: int) -> None:
    """删掉多余的最老备份。按文件名排序（时间戳前缀保证字典序=时间序）。"""
    backups = sorted(p for p in backup_dir.glob(f"{BACKUP_PREFIX}*.zip"))
    for old in backups[:-keep] if len(backups) > keep else []:
        try:
            old.unlink()
        except OSError:
            pass  # 清理是 best-effort


def list_backups(root: str | Path) -> list[Path]:
    """现有备份列表（时间升序）。"""
    backup_dir = Path(root) / BACKUP_DIRNAME
    if not backup_dir.is_dir():
        return []
    return sorted(backup_dir.glob(f"{BACKUP_PREFIX}*.zip"))


def restore(root: str | Path, backup_path: str | Path) -> int:
    """把备份恢复回 notes/（覆盖式）。返回恢复的文件数。

    恢复前把现有 notes/ 改名为 notes.broken-<ts>（不直接删——
    恢复操作本身可能出错，原名目录留着退路）。
    """
    root = Path(root)
    backup_path = Path(backup_path)
    if not backup_path.exists():
        raise FileNotFoundError(f"备份不存在: {backup_path}")

    notes_dir = root / "notes"
    if notes_dir.is_dir():
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        notes_dir.rename(root / f"notes.broken-{ts}")

    notes_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    with zipfile.ZipFile(backup_path) as zf:
        for info in zf.infolist():
            # 防路径穿越：成员名不允许 .. 与绝对路径
            if info.is_dir() or _unsafe_member(info.filename):
                continue
            target = notes_dir / info.filename
            target.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(info) as src, open(target, "wb") as dst:
                shutil.copyfileobj(src, dst)
            count += 1
    return count


def _unsafe_member(name: str) -> bool:
    """zip 成员名安全性（zip slip 防护）。"""
    normalized = name.replace("\\", "/")
    return normalized.startswith("/") or ".." in normalized.split("/")
