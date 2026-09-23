"""前缀树（M37）：笔记名的前缀导航。

list 长了想按键导航（输入 py 跳到第一个 py 开头的笔记）、
shell 里想补全笔记名——都需要前缀结构。

  Trie.insert / contains / starts_with
  complete(prefix, limit)     前缀补全（字典序前 limit 个）
  first_with(prefix)          前缀的第一个名字（导航跳转）
  from_names(names)           批量构建

通用数据结构实现（无笔记依赖），笔记名场景是消费者。
"""
from __future__ import annotations


class Trie:
    """字符前缀树（名字集合）。"""

    def __init__(self):
        self._root: dict = {}
        self._size = 0

    def __len__(self) -> int:
        return self._size

    def insert(self, name: str) -> None:
        node = self._root
        for ch in name:
            node = node.setdefault(ch, {})
        if "$" not in node:
            node["$"] = True
            self._size += 1

    def contains(self, name: str) -> bool:
        node = self._walk(name)
        return node is not None and "$" in node

    def starts_with(self, prefix: str) -> bool:
        return self._walk(prefix) is not None

    def complete(self, prefix: str, limit: int = 10) -> list[str]:
        """以 prefix 开头的名字（字典序，最多 limit 个）。"""
        node = self._walk(prefix)
        if node is None:
            return []
        out: list[str] = []
        self._collect(node, prefix, out, limit)
        return out

    def first_with(self, prefix: str) -> str | None:
        got = self.complete(prefix, limit=1)
        return got[0] if got else None

    def _walk(self, prefix: str):
        node = self._root
        for ch in prefix:
            if ch not in node:
                return None
            node = node[ch]
        return node

    def _collect(self, node: dict, prefix: str, out: list[str],
                 limit: int) -> None:
        if len(out) >= limit:
            return
        if "$" in node:
            out.append(prefix)
        for ch in sorted(k for k in node if k != "$"):
            if len(out) >= limit:
                return
            self._collect(node[ch], prefix + ch, out, limit)


def from_names(names) -> Trie:
    """批量构建。"""
    t = Trie()
    for n in names:
        t.insert(n)
    return t
