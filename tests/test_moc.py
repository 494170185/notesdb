"""M22 MOC 生成测试。"""
from notesdb.moc import (
    MIN_CLUSTER,
    build_moc_note,
    cluster_mocs,
    hub_candidates,
    render_moc,
)


def _notes():
    return {
        "hub": {"frontmatter": None, "body": ""},
        "a": {"frontmatter": {"tags": ["py"]}, "body": "[[hub]]"},
        "b": {"frontmatter": {"tags": ["py"]}, "body": "[[hub]]"},
        "c": {"frontmatter": {"tags": ["py"]}, "body": "[[hub]]"},
        "d": {"frontmatter": {"tags": ["cook"]}, "body": ""},
        "e": {"frontmatter": {"tags": ["cook"]}, "body": ""},
    }


def test_hub_candidates_ranked():
    hubs = hub_candidates(_notes())
    assert hubs[0] == {"name": "hub", "backlinks": 3}


def test_hub_candidates_excludes_zero():
    hubs = hub_candidates(_notes())
    assert all(h["backlinks"] > 0 for h in hubs)


def test_hub_candidates_top_limit():
    assert len(hub_candidates(_notes(), top=1)) == 1


def test_cluster_mocs_meets_min():
    """py 有 3 篇（≥MIN_CLUSTER）成 MOC；cook 只有 2 篇不成。"""
    mocs = cluster_mocs(_notes())
    assert list(mocs) == ["MOC: py"]
    assert set(mocs["MOC: py"]) == {"a", "b", "c"}


def test_cluster_mocs_custom_min():
    mocs = cluster_mocs(_notes(), min_cluster=2)
    assert set(mocs) == {"MOC: py", "MOC: cook"}


def test_cluster_mocs_empty():
    assert cluster_mocs({}) == {}


def test_render_moc_lists_members():
    text = render_moc("MOC: py", ["b", "a"])
    assert "[[a]]" in text and "[[b]]" in text
    assert text.startswith("# MOC: py")


def test_render_moc_empty():
    assert "暂无成员" in render_moc("MOC: x", [])


def test_build_moc_note_shape():
    note = build_moc_note("MOC: py", ["a"])
    assert note["frontmatter"]["tags"] == ["moc"]
    assert "[[a]]" in note["body"]


def test_min_cluster_default():
    assert MIN_CLUSTER == 3
