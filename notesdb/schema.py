"""frontmatter 架构（M32）：可选的字段类型校验。

库级可声明字段约定（notesdb.json 的 "schema" 键）：

  {"schema": {"date": "date", "rating": "int", "status": "enum"}}

字段类型：
  str / int / float / bool / date(ISO) / list / enum(可逗号列值)

用途：lint 的扩展检查项——frontmatter 声明了 date 却写成
"下周三"这类脏数据能被抓出来。**字段未声明不检查**（自由
字段是笔记工具的本性，schema 只管用户自己声明过的）。
"""
from __future__ import annotations

from datetime import date as _date

KNOWN_TYPES = {"str", "int", "float", "bool", "date", "list", "enum"}

_TYPE_CHECKS = {
    "str": lambda v: isinstance(v, str),
    "int": lambda v: isinstance(v, int) and not isinstance(v, bool),
    "float": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
    "bool": lambda v: isinstance(v, bool),
    "list": lambda v: isinstance(v, list),
}


class SchemaError(ValueError):
    """schema 声明本身不合法（类型名未知/枚举为空）。"""


def validate_schema(schema: dict) -> None:
    """schema 自检。坏声明抛 SchemaError（配置加载时用）。"""
    if not isinstance(schema, dict):
        raise SchemaError("schema 应为 {字段: 类型} 对象")
    for key, spec in schema.items():
        if not isinstance(key, str) or not key:
            raise SchemaError(f"schema 字段名应为非空字符串: {key!r}")
        if isinstance(spec, str):
            if spec not in KNOWN_TYPES:
                raise SchemaError(
                    f"字段 {key} 类型 {spec!r} 未知（支持 {sorted(KNOWN_TYPES)}）")
        elif isinstance(spec, list):
            if not spec or not all(isinstance(x, str) for x in spec):
                raise SchemaError(f"字段 {key} 的 enum 值列表应为非空字符串列表")
        else:
            raise SchemaError(f"字段 {key} 的类型声明应为字符串或枚举列表")


def check_value(field: str, value, spec) -> str | None:
    """校验单个字段值。返回错误消息或 None（合法）。

    None 值（字段显式置空）视为合法——"还没填"不是脏数据。
    """
    if value is None:
        return None
    if isinstance(spec, list):
        if not isinstance(value, str) or value not in spec:
            return f"应为 {spec} 之一，收到 {value!r}"
        return None
    if spec == "date":
        if not isinstance(value, str):
            return f"应为 ISO 日期字符串，收到 {type(value).__name__}"
        try:
            _date.fromisoformat(value)
        except ValueError:
            return f"应为 ISO 日期（YYYY-MM-DD），收到 {value!r}"
        return None
    check = _TYPE_CHECKS.get(spec)
    if check is None:
        return f"未知类型 {spec!r}"
    if not check(value):
        want = {"str": "字符串", "int": "整数", "float": "数值",
                "bool": "布尔", "list": "列表"}.get(spec, spec)
        return f"应为{want}，收到 {value!r}"
    return None


def check_note(note: dict, schema: dict) -> list[str]:
    """单篇笔记按 schema 检查。返回错误消息列表（空=通过）。"""
    fm = note.get("frontmatter") or {}
    errors = []
    for field, spec in schema.items():
        if field in fm:
            msg = check_value(field, fm[field], spec)
            if msg:
                errors.append(f"{field}: {msg}")
    return errors
