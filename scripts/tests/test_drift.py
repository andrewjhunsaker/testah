import json

from scripts.drift import append_changed, content_hash, detect, write_meta


def test_content_hash_ignores_blank_lines_and_edge_whitespace():
    assert content_hash("a\n\n  b  \n") == content_hash("a\nb")
    assert content_hash("a\nb") != content_hash("a\nc")


def test_detect_new_then_unchanged_then_changed(tmp_path):
    h1 = content_hash("first version")
    assert detect(tmp_path, h1) == "new"
    write_meta(tmp_path, "https://x.test/", h1, "2026-08-28T00:00:00Z")
    assert detect(tmp_path, h1) == "unchanged"
    assert detect(tmp_path, content_hash("second version")) == "changed"


def test_append_changed_dedups_per_page(tmp_path):
    p = tmp_path / "changed-pages.json"
    append_changed(p, "vizaeo", "home", "new")
    append_changed(p, "vizaeo", "home", "changed")
    append_changed(p, "vizaeo", "help", "changed")
    entries = json.loads(p.read_text())
    assert len(entries) == 2
    assert {"target": "vizaeo", "slug": "home", "status": "changed"} in entries
