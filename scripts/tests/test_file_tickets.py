from scripts.file_tickets import fileable, parse_draft, stamp_filed

DRAFT = """---
type: product-bug
target: vizaeo
source: page-maps/vizaeo/help
status: draft
---
# Fix the thing

It is broken.
"""


def test_parse_draft_extracts_meta_title_body():
    d = parse_draft(DRAFT)
    assert d["meta"]["type"] == "product-bug"
    assert d["meta"]["status"] == "draft"
    assert d["title"] == "Fix the thing"
    assert d["body"] == "It is broken."


def test_fileable_respects_status_implemented_and_filed():
    assert fileable({"status": "approved"}, all_drafts=False)
    assert not fileable({"status": "draft"}, all_drafts=False)
    assert fileable({"status": "draft"}, all_drafts=True)
    assert fileable({"status": "scout-observed"}, all_drafts=True)
    assert not fileable({"status": "scout-observed"}, all_drafts=False)
    assert not fileable({"status": "filed:TES-1"}, all_drafts=True)
    assert not fileable(
        {"status": "draft", "implemented": "requirements/x.md"}, all_drafts=True
    )


def test_stamp_filed_rewrites_only_status_line():
    stamped = stamp_filed(DRAFT, "TES-7")
    assert "status: filed:TES-7" in stamped
    assert stamped.count("status:") == 1
    assert "# Fix the thing" in stamped
