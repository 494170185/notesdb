"""库缓存与变更检测（M23）：避免每次命令全量重读磁盘。

CLI 每个子命令都 load() 全库——库到几千篇时列表命令
也开始拖。本模块做两层：

  LibraryCache
    load() 后缓存 (notes, errors)；stat 变化（目录 mtime +
    文件数 + 总大小）才重新加载。单进程内多个命令复用。

  scan_changes(root, known_mtimes)
    给外部（watcher/同步）用的增量：对比已知 mtime 表，
    返回 {added, modified, removed}。

不做文件系统事件监听（watchdog 依赖）：轮询 stat 足够
（笔记库不是高频写入场景），且保持零依赖。
"""
from __future__ import annotations

import os
from pathlib import Path

from .store import Store


class LibraryCache:
    """单进程内的库缓存。"""

    def __init__(self, root: str | os.PathLike):
        self.root = Path(root)
        self._store = Store(root)
        self._notes: dict[str, dict] | None = None
        self._errors: list[str] | None = None
        self._fingerprint: tuple | None = None

    def load(self) -> tuple[dict[str, dict], list[str]]:
        """带缓存的加载。目录指纹不变时直接返回缓存。"""
        fp = self.fingerprint()
        if self._notes is not None and fp == self._fingerprint:
            return self._notes, self._errors or []
        self._notes, self._errors = self._store.load()
        self._fingerprint = fp
        return self._notes, self._errors

    def fingerprint(self) -> tuple:
        """库状态指纹（mtime, 文件数, 总字节数）。变更 → 不同。"""
        notes_dir = self.root / "notes"
        if not notes_dir.is_dir():
            return ()
        count = 0
        total = 0
        latest = 0.0
        for p in notes_dir.rglob("*.md"):
            try:
                st = p.stat()
            except OSError:
                continue
            count += 1
            total += st.st_size
            latest = max(latest, st.st_mtime)
        return (round(latest, 6), count, total)

    def invalidate(self) -> None:
        """显式弃缓存（写操作后调用）。"""
        self._notes = None
        self._errors = None
        self._fingerprint = None


def scan_changes(root: str | os.PathLike,
                 known: dict[str, float]) -> dict[str, list]:
    """对比已知 mtime 表，找出增删改。

    known: {name: mtime}（上次扫描的快照）。
    返回 {"added": [names], "modified": [names], "removed": [names]}。
    """
    store = Store(root)
    notes, _ = store.load()

    # 当前 mtime 快照
    current: dict[str, float] = {}
    for name in notes:
        p = store.path_of(name)
        try:
            current[name] = p.stat().st_mtime
        except OSError:
            current[name] = 0.0

    added = sorted(set(current) - set(known))
    removed = sorted(set(known) - set(current))
    modified = sorted(
        n for n in set(current) & set(known)
        if current[n] != known[n])
    return {"added": added, "modified": modified, "removed": removed}
