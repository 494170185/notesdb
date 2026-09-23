"""配置文件（M14）：notesdb.json 让用户按库自定义行为。

无配置时一切用默认值（零配置开箱即用）；有配置时覆盖默认。
字段（全部可选）：
  index_threshold    相似笔记阈值（默认 0.2）
  export_dir         导出目录名（默认 "export"）
  backup_keep        备份保留数（默认 10）
  exclude            不参与索引/导出的笔记名 glob 列表
  daily_template     新建每日笔记时的模板正文

加载口径：
- 文件不存在 → 全默认（不是错误）；
- JSON 坏 → ConfigError（配置是用户显式写的，错了必须报，
  静默回退会让用户以为配置生效了）；
- 未知键 → ConfigError（同上，拼错键名静默忽略最坑）；
- 类型不对 → ConfigError。

环境变量 NDB_<KEY> 再覆盖一层（CI/脚本场景）。
"""
from __future__ import annotations

import fnmatch
import json
import os
from dataclasses import dataclass, field
from pathlib import Path

CONFIG_FILENAME = "notesdb.json"
ENV_PREFIX = "NDB_"


class ConfigError(ValueError):
    """配置文件错误（消息面向用户）。"""


@dataclass
class Config:
    """库级配置（全部有默认值）。"""

    index_threshold: float = 0.2
    export_dir: str = "export"
    backup_keep: int = 10
    exclude: list[str] = field(default_factory=list)
    daily_template: str = ""

    def is_excluded(self, name: str) -> bool:
        """笔记名是否被 exclude glob 排除。"""
        return any(fnmatch.fnmatch(name, pat) for pat in self.exclude)


_DEFAULTS = {
    "index_threshold": 0.2,
    "export_dir": "export",
    "backup_keep": 10,
    "exclude": [],
    "daily_template": "",
}

_TYPES = {
    "index_threshold": float,
    "export_dir": str,
    "backup_keep": int,
    "exclude": list,
    "daily_template": str,
}


def load(root: str | Path, env: dict | None = None) -> Config:
    """加载配置：默认值 < notesdb.json < 环境变量 NDB_*。"""
    values = dict(_DEFAULTS)
    path = Path(root) / CONFIG_FILENAME
    if path.exists():
        try:
            with open(path, encoding="utf-8") as f:
                user = json.load(f)
        except json.JSONDecodeError as e:
            raise ConfigError(f"{CONFIG_FILENAME} 不是合法 JSON: {e}") from None
        if not isinstance(user, dict):
            raise ConfigError(f"{CONFIG_FILENAME} 顶层必须是对象")
        unknown = set(user) - set(_DEFAULTS)
        if unknown:
            raise ConfigError(f"未知配置键: {sorted(unknown)}")
        values.update(user)
    _apply_env(values, env if env is not None else dict(os.environ))
    _validate(values)
    return Config(**values)


def _apply_env(values: dict, env: dict) -> None:
    for key in _DEFAULTS:
        raw = env.get(f"{ENV_PREFIX}{key.upper()}")
        if raw is None or raw == "":
            continue
        if isinstance(_DEFAULTS[key], float):
            values[key] = float(raw)
        elif isinstance(_DEFAULTS[key], int):
            values[key] = int(raw)
        elif isinstance(_DEFAULTS[key], list):
            values[key] = [s.strip() for s in raw.split(",") if s.strip()]
        else:
            values[key] = raw


def _validate(values: dict) -> None:
    for key, want in _TYPES.items():
        got = values[key]
        if want is float and isinstance(got, (int, float)) and not isinstance(got, bool):
            continue
        if want is int and isinstance(got, int) and not isinstance(got, bool):
            continue
        if want is list and isinstance(got, list) and all(isinstance(x, str) for x in got):
            continue
        if want is str and isinstance(got, str):
            continue
        raise ConfigError(f"配置 {key} 类型应为 {want.__name__}，收到 {type(got).__name__}")
    if not (0 < values["index_threshold"] <= 1):
        raise ConfigError(f"index_threshold 应在 (0, 1]，收到 {values['index_threshold']}")
    if values["backup_keep"] < 0:
        raise ConfigError(f"backup_keep 不能为负，收到 {values['backup_keep']}")
