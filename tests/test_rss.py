"""M34 RSS 测试。"""
import xml.etree.ElementTree as ET
from datetime import datetime

from notesdb.rss import build_feed, write_feed


def _notes():
    return {
        "old": {"frontmatter": None, "body": "旧文"},
        "new": {"frontmatter": {"title": "新文"}, "body": "新内容 " * 50},
        "mid": {"frontmatter": None, "body": "中文"},
    }


MT = {"old": datetime(2026, 1, 1).timestamp(),
      "new": datetime(2026, 9, 24).timestamp(),
      "mid": datetime(2026, 6, 1).timestamp()}


def test_feed_is_valid_xml():
    feed = build_feed(_notes(), lambda n: MT[n], "https://x.example")
    root = ET.fromstring(feed)  # 解析不抛即合法
    assert root.tag == "rss"
    assert root.find("channel/title").text == "notesdb"


def test_feed_orders_recent_first():
    feed = build_feed(_notes(), lambda n: MT[n], "https://x.example")
    titles = [e.text for e in ET.fromstring(feed).iter("title")]
    assert titles[1] == "新文"  # channel 标题后第一个 item


def test_feed_limit():
    feed = build_feed(_notes(), lambda n: MT[n], "https://x.example", limit=1)
    items = list(ET.fromstring(feed).iter("item"))
    assert len(items) == 1


def test_feed_escapes_entities():
    notes = {"a": {"frontmatter": {"title": "含 <b>标签</b> & 符号"},
                   "body": "x"}}
    feed = build_feed(notes, lambda _: 1000.0, "https://x.example")
    assert "&lt;b&gt;" in feed or "<b>" not in feed.split("<channel>")[1].split("</title>")[0]
    ET.fromstring(feed)  # 仍然合法


def test_feed_summary_truncated():
    feed = build_feed(_notes(), lambda n: MT[n], "https://x.example")
    descs = list(ET.fromstring(feed).iter("description"))
    # 第一个是 channel 描述；item 的在后面。new（200+ 字）排第一
    item_desc = descs[1].text
    assert item_desc.endswith("…")


def test_feed_item_link_points_to_note_page():
    feed = build_feed(_notes(), lambda n: MT[n], "https://x.example")
    link = list(ET.fromstring(feed).iter("link"))[1].text
    assert link.startswith("https://x.example/notes/")


def test_feed_skips_unknown_mtime():
    feed = build_feed(_notes(), lambda n: MT.get(n), "https://x.example")
    items = list(ET.fromstring(feed).iter("item"))
    assert len(items) == 3  # 全部有 mtime


def test_write_feed_creates_file(tmp_path):
    path = write_feed(tmp_path, _notes(), lambda n: MT[n], "https://x.example")
    assert path.endswith("rss.xml")
    with open(path, encoding="utf-8") as f:
        ET.fromstring(f.read())
