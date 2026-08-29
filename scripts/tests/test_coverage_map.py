from pathlib import Path

from scripts.coverage_map import parse_frontmatter, run_outcomes, spec_links


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


def test_parse_frontmatter_reads_keys_and_tolerates_absence():
    assert parse_frontmatter("---\napproved: false\ntype: x\n---\nbody") == {
        "approved": "false",
        "type": "x",
    }
    assert parse_frontmatter("no frontmatter here") == {}
