"""M8 库健康校验测试。"""
from notesdb.lint import Issue, check_library, has_errors


def _n(fm_error=False, body="content", front=None, **fm):
    frontmatter = dict(fm) if fm else front
    note = {"frontmatter": frontmatter, "body": body,
            "frontmatter_error": fm_error}
    return note


# ---------------------------------------------------------------- 单项

def test_healthy_library_no_issues():
    notes = {"a": _n(body="text [[b]]"), "b": _n(body="back [[a]]")}
    assert check_library(notes) == []


def test_bad_frontmatter_is_error():
    notes = {"a": _n(fm_error=True)}
    issues = check_library(notes)
    assert any(i.severity == "error" and i.check == "bad_frontmatter"
               for i in issues)


def test_empty_body_is_warning():
    issues = check_library({"a": _n(body="   ")})
    assert any(i.severity == "warning" and i.check == "empty_note"
               for i in issues)


def test_duplicate_title_is_warning():
    notes = {
        "a": _n(title="Same"),
        "b": _n(title="Same"),
    }
    issues = check_library(notes)
    assert any(i.check == "title_dup" and "Same" in i.message for i in issues)


def test_name_case_conflict_is_error():
    notes = {"Readme": _n(), "README": _n()}
    issues = check_library(notes)
    assert any(i.severity == "error" and i.check == "name_conflict"
               for i in issues)


def test_dangling_link_reported():
    notes = {"a": _n(body="[[ghost]]")}
    issues = check_library(notes)
    assert any(i.check == "dangling_links" and "ghost" in i.message
               for i in issues)


def test_orphan_reported():
    issues = check_library({"alone": _n()})
    assert any(i.check == "orphan_notes" and i.note == "alone"
               for i in issues)


def test_broken_template_reported():
    issues = check_library({"a": _n(body="{{undefined_key}}")})
    assert any(i.check == "broken_template" and "undefined_key" in i.message
               for i in issues)


# ---------------------------------------------------------------- 组合

def test_has_errors_false_when_only_warnings():
    notes = {"a": _n(body="")}
    assert not has_errors(check_library(notes))


def test_has_errors_true():
    notes = {"a": _n(fm_error=True)}
    assert has_errors(check_library(notes))


def test_issue_str_format():
    i = Issue("error", "bad_frontmatter", "note1", "YAML 坏了")
    assert "bad_frontmatter" in str(i) and "note1" in str(i)
    lib = Issue("warning", "x", "", "库级")
    assert "x" in str(lib)


def test_all_checks_ordered_deterministically():
    """同样输入跑两遍结果一致（排序稳定，导出/CI 可比对）。"""
    notes = {"z": _n(body="[[x]]"), "x": _n(fm_error=True), "m": _n(body="")}
    r1 = [str(i) for i in check_library(notes)]
    r2 = [str(i) for i in check_library(notes)]
    assert r1 == r2
