from pathlib import Path

from scripts.coverage_map import (
    feature_notes,
    parse_frontmatter,
    run_outcomes,
    spec_links,
    tests_by_spec,
)


def test_spec_links_reads_implements_headers(tmp_path):
    specs = tmp_path / "specs"
    specs.mkdir()
    (specs / "a.spec.ts").write_text(
        "// implements: requirements/t/p/f.md\nimport x\n", encoding="utf-8"
    )
    (specs / "scaffold.spec.ts").write_text("import x\n", encoding="utf-8")
    links = spec_links(specs)
    assert links["a.spec.ts"] == "requirements/t/p/f.md"
    assert links["scaffold.spec.ts"] is None


def test_run_outcomes_worst_status_wins_per_file():
    report = {
        "suites": [
            {
                "title": "a.spec.ts",
                "specs": [
                    {"title": "one", "tests": [{"status": "expected"}]},
                    {"title": "two", "tests": [{"status": "flaky"}]},
                    {"title": "three", "tests": [{"status": "unexpected"}]},
                ],
            },
            {
                "title": "b.spec.ts",
                "specs": [{"title": "only", "tests": [{"status": "flaky"}]}],
            },
        ]
    }
    outcomes = run_outcomes(report)
    assert outcomes["a.spec.ts"] == "fail"
    assert outcomes["b.spec.ts"] == "flaky"


def test_tests_by_spec_groups_individual_tests_and_maps_status():
    report = {
        "suites": [
            {
                "title": "a.spec.ts",
                "suites": [
                    {
                        "title": "/help — grid",
                        "specs": [
                            {
                                "title": "one",
                                "tests": [
                                    {"status": "expected", "projectName": "chromium"}
                                ],
                            },
                            {
                                "title": "two",
                                "tests": [
                                    {"status": "unexpected", "projectName": "chromium"}
                                ],
                            },
                        ],
                    }
                ],
            },
            {
                "title": "b.spec.ts",
                "specs": [{"title": "solo", "tests": [{"status": "flaky"}]}],
            },
        ]
    }
    grouped = tests_by_spec(report)
    assert [t["title"] for t in grouped["a.spec.ts"]] == [
        "/help — grid › one",
        "/help — grid › two",
    ]
    assert [t["status"] for t in grouped["a.spec.ts"]] == ["pass", "fail"]
    assert grouped["a.spec.ts"][0]["id"] == "a.spec.ts > /help — grid > one > chromium"
    assert grouped["b.spec.ts"] == [
        {"title": "solo", "status": "flaky", "id": "b.spec.ts > solo"}
    ]


def test_feature_notes_separate_draft_pending_approval_and_clean():
    draft = {
        "status": "draft",
        "approved": "draft",
        "requirements": None,
        "flaky_over_threshold": False,
    }
    assert feature_notes(draft) == ["ticket draft only — no criteria or tests yet"]

    awaiting = {
        "status": "criteria-only",
        "approved": "false",
        "requirements": "requirements/t/p/f.md",
        "flaky_over_threshold": False,
    }
    assert feature_notes(awaiting) == [
        "criteria awaiting your approval — see Judgment calls in "
        "requirements/t/p/f.md"
    ]

    covered_but_unapproved = dict(awaiting, status="pass")
    assert feature_notes(covered_but_unapproved) == feature_notes(awaiting)

    clean = dict(awaiting, status="pass", approved="true")
    assert feature_notes(clean) == []
    assert feature_notes(dict(clean, flaky_over_threshold=True)) == [
        "⚠ over flake threshold"
    ]


def test_parse_frontmatter_reads_keys_and_tolerates_absence():
    assert parse_frontmatter("---\napproved: false\ntype: x\n---\nbody") == {
        "approved": "false",
        "type": "x",
    }
    assert parse_frontmatter("no frontmatter here") == {}
