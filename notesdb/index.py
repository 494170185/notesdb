"""全文倒排索引（M3）：词元 → 出现该词元的笔记集合。

结构（内存 dict，库规模万级笔记内不需要外部引擎）：
  index[token] = {note_name: [posting, ...]}
  posting = (line_no, char_offset, token_len)   # 标题记 (-1, -1, len)

字符偏移让短语判定可行：相邻词元的偏移差恰为前一词元长度
加空白（允许 [0,3] 字符的间隙），就能确认它们在原文里真正
相邻且保序——行级粒度判不了顺序。

查询接口：
  search(word)          → 词元精确命中（多词元 AND）
  search_prefix(word)   → 前缀命中（英文 "proj" 匹配 "project"）
  search_phrase(phrase) → 短语命中（偏移连续性判定，保序）

索引与查询共用 tokenize（"怎么建就怎么查"）。
"""
from __future__ import annotations

import re
from collections import defaultdict

from .model import note_title
from .tokenize import tokenize

_WORD_RE = re.compile(r"[A-Za-z0-9]+(?:'[A-Za-z]+)*")
_HAN_SEG_RE = re.compile(r"[\u4e00-\u9fff\u3400-\u4dbf]+")

# 短语内相邻词元之间允许的最大空白字符数
_MAX_GAP = 3


class InvertedIndex:
    """带位置（行号+偏移+词长）的倒排索引。"""

    def __init__(self):
        # token -> {note_name: [(line, offset, token_len), ...]}
        self._index: dict[str, dict[str, list[tuple[int, int, int]]]] = defaultdict(dict)

    def build(self, notes: dict[str, dict]) -> None:
        """全量重建（覆盖旧内容）。"""
        self._index = defaultdict(dict)
        for name, note in notes.items():
            self._add_note(name, note)

    def _add_note(self, name: str, note: dict) -> None:
        # 标题（frontmatter.title 或笔记名）也参与索引——
        # 用户搜标题必须能命中。标题位置记 (-1, -1, len)。
        title = note_title(note) or name
        for token in tokenize(title):
            self._index[token].setdefault(name, []).append((-1, -1, len(token)))
        for line_no, line in enumerate(note.get("body", "").splitlines()):
            for token, offset in _line_tokens_with_offsets(line):
                self._index[token].setdefault(name, []).append(
                    (line_no, offset, len(token)))

    # ---------------------------------------------------------------- 查询

    def search(self, word: str) -> dict[str, list[int]]:
        """词元精确命中，返回 {name: [行号...]}（去重升序）。

        多词元查询（"hello world"）取 AND 语义。
        """
        tokens = tokenize(word)
        if not tokens:
            return {}
        result: dict[str, set[int]] | None = None
        for t in tokens:
            hits: dict[str, set[int]] = {
                n: {ln for ln, _, _ in postings}
                for n, postings in self._index.get(t, {}).items()
            }
            if result is None:
                result = hits
            else:
                result = {n: result[n] & hits[n] for n in result if n in hits}
        return {n: sorted(v) for n, v in (result or {}).items() if v}

    def search_prefix(self, word: str) -> dict[str, list[int]]:
        """前缀命中：合并所有以查询前缀开头的词元。"""
        tokens = tokenize(word)
        if not tokens:
            return {}
        prefix = tokens[0]
        merged: dict[str, set[int]] = defaultdict(set)
        for token, hits in self._index.items():
            if token.startswith(prefix):
                for name, postings in hits.items():
                    merged[name].update(ln for ln, _, _ in postings)
        return {n: sorted(v) for n, v in merged.items() if v}

    def search_phrase(self, phrase: str) -> dict[str, list[int]]:
        """短语命中：偏移连续性判定（词元在原文中真正相邻且保序）。"""
        tokens = tokenize(phrase)
        if not tokens:
            return {}
        per_token = [self._index.get(t, {}) for t in tokens]
        if not per_token[0]:
            return {}
        candidates = set(per_token[0])
        for hits in per_token[1:]:
            candidates &= set(hits)
        out: dict[str, list[int]] = {}
        for name in candidates:
            postings = [hits[name] for hits in per_token]
            if _phrase_occurs(postings):
                lines = sorted({ln for p in postings for ln, _, _ in p if ln >= 0})
                out[name] = lines
        return out

    def stats(self) -> dict:
        """索引统计（供报表）。"""
        total_postings = sum(len(names) for names in self._index.values())
        return {"vocabulary": len(self._index), "postings": total_postings}


def _line_tokens_with_offsets(line: str) -> list[tuple[str, int]]:
    """一行文本的 (词元, 偏移) 序列，按出现序。"""
    out: list[tuple[str, int]] = []
    for m in _WORD_RE.finditer(line):
        out.append((m.group(0).lower(), m.start()))
    for m in _HAN_SEG_RE.finditer(line):
        seg, start = m.group(0), m.start()
        for i in range(len(seg) - 1):
            out.append((seg[i:i + 2], start + i))
        if len(seg) == 1:
            out.append((seg, start))
    out.sort(key=lambda x: x[1])
    return out


def _phrase_occurs(postings_per_token: list[list[tuple[int, int, int]]]) -> bool:
    """判定短语是否真实出现（词元序列在原文相邻且保序）。

    postings_per_token[i] 是第 i 个词元在候选笔记的全部位置。
    逐个尝试第一个词元的每个出现位置，向后贪心匹配，相邻的
    两种合法形态：
      1. bigram 步进：off - cur_off == 1（中文 bigram 词元天然
         重叠一个字符，"全文检索" 的 全文/文检/检索 就是步进 1）；
      2. 不重叠相邻：off - (cur_off + cur_len) ∈ [0, _MAX_GAP]
         （英文词元或间隔了标点的中文）。
    """
    for start_ln, start_off, start_len in postings_per_token[0]:
        cur_ln, cur_off, cur_len = start_ln, start_off, start_len
        ok = True
        for i in range(1, len(postings_per_token)):
            matched = False
            for ln, off, length in postings_per_token[i]:
                if ln != cur_ln or off <= cur_off:
                    continue
                step = off - cur_off
                adjacent = step == 1 or 0 <= off - (cur_off + cur_len) <= _MAX_GAP
                if adjacent:
                    cur_off, cur_len = off, length
                    matched = True
                    break
            if not matched:
                ok = False
                break
        if ok:
            return True
    return False
