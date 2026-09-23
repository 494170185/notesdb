"""JSON 交换格式（M43）：整库导出/导入为单文件 JSON。

跨机迁移、给外部工具消费的稳定格式：

  export_json(notes)        {version, exported_at, notes: [...]}
  import_json(text, notes, mode)   合并回库（skip/suffix/overwrite
                            语义与 M17 目录导入一致）

版本字段：格式演进时的兼容判断锚点（v1 丢弃未知字段时
报警而不是崩）。
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

FORMAT_VERSION = 1


def export_json(notes: dict[str, dict]) -> str:
    """导出为 JSON 文本（ensure_ascii=False，人可读）。"""
    payload = {
        "version": FORMAT_VERSION,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "notes": [
            {"name": name,
             "frontmatter": note.get("frontmatter"),
             "body": note.get("body", "")}
            for name in sorted(notes)
        ],
    }
    return json.dumps(payload, ensure_ascii=False, indent=1)


def import_json(text: str, existing: dict[str, dict],
                mode: str = "skip") -> dict:
    """把 JSON 导入回 {name: note} 集合。

    existing 是当前库；返回**新集合**（不修改入参）。
    mode 语义同 importer：skip/suffix/overwrite。
    """
    if mode not in ("skip", "suffix", "overwrite"):
        raise ValueError(f"mode 只支持 skip/suffix/overwrite，收到 {mode!r}")
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"不是合法 JSON: {e}") from None
    if not isinstance(payload, dict) or "notes" not in payload:
        raise ValueError("JSON 结构不对：缺 notes 字段")
    version = payload.get("version")
    if version != FORMAT_VERSION:
        raise ValueError(f"格式版本 {version!r} 不支持（当前 {FORMAT_VERSION}）")

    merged = {name: note for name, note in existing.items()}
    for item in payload["notes"]:
        name = item.get("name")
        if not name:
            continue
        note = {"frontmatter": item.get("frontmatter"),
                "body": item.get("body", "")}
        if name in merged:
            if mode == "skip":
                continue
            if mode == "suffix":
                k = 2
                new_name = f"{name}-imported"
                while new_name in merged:
                    new_name = f"{name}-imported-{k}"
                    k += 1
                name = new_name
        merged[name] = note
    return merged
