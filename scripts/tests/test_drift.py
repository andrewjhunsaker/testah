import json

from scripts.drift import (
    append_changed,
    content_hash,
    detect,
    page_content,
    write_meta,
)


def test_content_hash_ignores_trailing_whitespace_only():
    assert content_hash("a\nb  ") == content_hash("a\nb")
    assert content_hash("a\n  b") != content_hash("a\nb")  # indentation is structure
    assert content_hash("a\n\nb") != content_hash("a\nb")  # blank lines are structure
    assert content_hash("a\nb") != content_hash("a\nc")


def test_page_content_includes_structure(tmp_path):
    (tmp_path / "page.md").write_text("same text", encoding="utf-8")
    (tmp_path / "page.json").write_text('{"buttons": []}', encoding="utf-8")
    before = content_hash(page_content(tmp_path))
    (tmp_path / "page.json").write_text('{"buttons": ["x"]}', encoding="utf-8")
    assert content_hash(page_content(tmp_path)) != before


def test_detect_new_then_unchanged_then_changed(tmp_path):
    h1 = content_hash("first version")
    assert detect(tmp_path, h1) == "new"
    write_meta(tmp_path, "https://x.test/", h1, "2026-08-28T00:00:00Z")
    assert detect(tmp_path, h1) == "unchanged"
    assert detect(tmp_path, content_hash("second version")) == "changed"


def test_append_changed_dedups_and_new_is_sticky(tmp_path):
    p = tmp_path / "changed-pages.json"
    append_changed(p, "vizaeo", "home", "new")
    append_changed(p, "vizaeo", "home", "changed")
    append_changed(p, "vizaeo", "help", "changed")
    entries = json.loads(p.read_text())
    assert len(entries) == 2
    assert {"target": "vizaeo", "slug": "home", "status": "new"} in entries
    assert {"target": "vizaeo", "slug": "help", "status": "changed"} in entries
