import json
import subprocess
from pathlib import Path

import pytest

from dashboard.snapshot import build_snapshot, snapshot_version, source_provenance


COMPLETED_REPORT = {
    "config": {
        "metadata": {"testah": {"baseURL": "https://app.example.test"}},
    },
    "errors": [],
    "stats": {
        "startTime": "2026-08-28T17:11:39.230Z",
        "duration": 14404.824,
        "expected": 33,
        "unexpected": 1,
        "flaky": 0,
        "skipped": 0,
    },
}


def write_completed_report(repo: Path, *, passed: int, failed: int) -> None:
    """Replace fixture report counts with complete dashboard evidence."""
    report = completed_report(repo)
    report["stats"] = {
        **COMPLETED_REPORT["stats"],
        "expected": passed,
        "unexpected": failed,
    }
    (repo / "reports" / "last-run.json").write_text(json.dumps(report), encoding="utf-8")


def completed_report(repo: Path) -> dict:
    """Return complete report evidence stamped with its producing sources."""
    report = json.loads(json.dumps(COMPLETED_REPORT))
    report["config"]["metadata"]["testah"].update(source_provenance(repo))
    return report


def fixture_repository(
    tmp_path: Path,
    *,
    with_report: bool,
    report_case: str = "completed",
    target_count: int = 1,
) -> Path:
    """Create a minimal repository whose dashboard evidence is complete."""
    repo = tmp_path / "fixture-repository"
    repo.mkdir()
    targets = """targets:
  example:
    name: Example target
    base_url: https://app.example.test
"""
    if target_count == 2:
        targets += """  other:
    name: Other
    base_url: https://other.example.com
"""
    (repo / "targets.yaml").write_text(
        targets,
        encoding="utf-8",
    )
    (repo / "tests" / "specs").mkdir(parents=True)
    (repo / "tests" / "specs" / "smoke.spec.ts").write_text(
        "test('smoke', () => {});\n", encoding="utf-8"
    )
    (repo / "requirements").mkdir()
    (repo / "requirements" / "smoke.md").write_text(
        "# Smoke requirement\n", encoding="utf-8"
    )
    playwright_config = repo / "playwright.config.ts"
    playwright_config.write_text("export default {};\n", encoding="utf-8")
    subprocess.run(["git", "init", "-b", "master"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Fixture User"], cwd=repo, check=True)
    subprocess.run(
        ["git", "config", "user.email", "fixture@example.com"], cwd=repo, check=True
    )
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "fixture"], cwd=repo, check=True)
    if with_report:
        (repo / "reports").mkdir()
        report_path = repo / "reports" / "last-run.json"
        if report_case == "malformed":
            report_path.write_text("not json", encoding="utf-8")
        else:
            report = completed_report(repo)
            if report_case == "incomplete":
                report = {"stats": {"expected": 33}}
            elif report_case == "unattributed":
                report["config"]["metadata"]["testah"]["baseURL"] = (
                    "https://unknown.example"
                )
            report_path.write_text(json.dumps(report), encoding="utf-8")
            if report_case == "older-than-sources":
                source_path = repo / "tests" / "specs" / "smoke.spec.ts"
                source_path.write_text("test('changed', () => {});\n", encoding="utf-8")
            if report_case == "older-than-playwright-config":
                playwright_config.write_text("export default { changed: true };\n")
    return repo


def test_current_snapshot_is_built_from_a_fixture_repository(tmp_path):
    """A configured report is exposed as its normalized domain snapshot."""
    repo = fixture_repository(tmp_path, with_report=True)
    snapshot = build_snapshot(repo)

    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, check=True, text=True, capture_output=True
    ).stdout.strip()
    assert snapshot["repository"] == {"branch": "master", "commit": commit}
    assert snapshot["targets"] == [
        {
            "key": "example",
            "name": "Example target",
            "base_url": "https://app.example.test",
            "environment": None,
            "latest_run": {
                "state": "completed",
                "started_at": "2026-08-28T17:11:39.230Z",
                "duration_ms": 14404.824,
                "counts": {"passed": 33, "failed": 1, "flaky": 0, "skipped": 0},
            },
        }
    ]


@pytest.mark.parametrize("constant", ["NaN", "Infinity", "-Infinity"])
def test_snapshot_rejects_non_standard_json_constants(constant, tmp_path):
    """Non-standard JSON numbers make the report unavailable in the snapshot."""
    repo = fixture_repository(tmp_path, with_report=True)
    report_path = repo / "reports" / "last-run.json"
    report = json.dumps(completed_report(repo)).replace("14404.824", constant, 1)
    report_path.write_text(report, encoding="utf-8")

    target = build_snapshot(repo)["targets"][0]

    assert target["latest_run"]["state"] == "unavailable"
    assert target["latest_run"]["duration_ms"] is None


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("expected", True),
        ("expected", -1),
        ("expected", 1.5),
        ("duration", True),
        ("duration", -1),
        ("startTime", "not-a-timestamp"),
    ],
)
def test_snapshot_rejects_structurally_invalid_report_values(field, value, tmp_path):
    """Invalid count, duration, and timestamp values stay incomplete, not healthy."""
    repo = fixture_repository(tmp_path, with_report=True)
    report = {
        **completed_report(repo),
        "stats": {**COMPLETED_REPORT["stats"], field: value},
    }
    (repo / "reports" / "last-run.json").write_text(
        json.dumps(report), encoding="utf-8"
    )

    latest_run = build_snapshot(repo)["targets"][0]["latest_run"]

    assert latest_run["state"] == "incomplete"
    if field == "expected":
        assert latest_run["counts"]["passed"] is None
    elif field == "duration":
        assert latest_run["duration_ms"] is None
    else:
        assert latest_run["started_at"] is None


def test_top_level_playwright_errors_prevent_completed_evidence(tmp_path):
    """A runner-level failure cannot be presented as a completed test run."""
    repo = fixture_repository(tmp_path, with_report=True)
    report = {
        **completed_report(repo),
        "errors": [{"message": "global setup failed"}],
    }
    (repo / "reports" / "last-run.json").write_text(
        json.dumps(report), encoding="utf-8"
    )

    latest_run = build_snapshot(repo)["targets"][0]["latest_run"]

    assert latest_run["state"] == "incomplete"
    assert latest_run["counts"] == {
        "passed": 33,
        "failed": 1,
        "flaky": 0,
        "skipped": 0,
    }


def test_snapshot_normalizes_iso_start_time(tmp_path):
    """A valid report timestamp is returned as a normalized UTC ISO timestamp."""
    repo = fixture_repository(tmp_path, with_report=True)
    report = {
        **completed_report(repo),
        "stats": {
            **COMPLETED_REPORT["stats"],
            "startTime": "2026-08-28T19:11:39.230+02:00",
        },
    }
    (repo / "reports" / "last-run.json").write_text(
        json.dumps(report), encoding="utf-8"
    )

    latest_run = build_snapshot(repo)["targets"][0]["latest_run"]

    assert latest_run["state"] == "completed"
    assert latest_run["started_at"] == "2026-08-28T17:11:39.230Z"


@pytest.mark.parametrize(
    ("report_case", "expected_state"),
    [
        ("missing", "never-run"),
        ("incomplete", "incomplete"),
        ("malformed", "unavailable"),
        ("older-than-sources", "stale"),
        ("older-than-playwright-config", "stale"),
        ("unattributed", "partial"),
    ],
)
def test_snapshot_preserves_evidence_state(report_case, expected_state, tmp_path):
    """Each unavailable or imperfect report remains visibly distinguished."""
    repo = fixture_repository(
        tmp_path,
        with_report=report_case != "missing",
        report_case=report_case,
        target_count=2 if report_case == "unattributed" else 1,
    )

    target = build_snapshot(repo)["targets"][0]

    assert target["latest_run"]["state"] == expected_state


def test_single_target_report_requires_matching_target_identity(tmp_path):
    """A report from an overridden host is not attributed by target count alone."""
    repo = fixture_repository(
        tmp_path,
        with_report=True,
        report_case="unattributed",
        target_count=1,
    )

    target = build_snapshot(repo)["targets"][0]

    assert target["latest_run"]["state"] == "partial"
    assert target["latest_run"]["counts"] == {
        "passed": 33,
        "failed": 1,
        "flaky": 0,
        "skipped": 0,
    }


def test_incomplete_report_is_only_attached_to_its_recorded_target(tmp_path):
    """Partial statistics never leak onto another configured target."""
    repo = fixture_repository(tmp_path, with_report=True, target_count=2)
    report = {
        **completed_report(repo),
        "stats": {**COMPLETED_REPORT["stats"], "expected": None},
    }
    (repo / "reports" / "last-run.json").write_text(
        json.dumps(report), encoding="utf-8"
    )

    targets = build_snapshot(repo)["targets"]

    assert targets[0]["latest_run"]["state"] == "incomplete"
    assert targets[0]["latest_run"]["counts"]["failed"] == 1
    assert targets[1]["latest_run"] == {
        "state": "never-run",
        "started_at": None,
        "duration_ms": None,
        "counts": None,
    }


def test_recorded_target_metadata_wins_over_unrelated_report_urls(tmp_path):
    """Failure text mentioning another target cannot override producer metadata."""
    repo = fixture_repository(tmp_path, with_report=True, target_count=2)
    report = {
        **completed_report(repo),
        "suites": [{"title": "https://other.example.com"}],
    }
    (repo / "reports" / "last-run.json").write_text(
        json.dumps(report), encoding="utf-8"
    )

    targets = build_snapshot(repo)["targets"]

    assert targets[0]["latest_run"]["state"] == "completed"
    assert targets[1]["latest_run"]["state"] == "never-run"


def test_snapshot_version_changes_with_dashboard_evidence(tmp_path):
    """A report rewrite changes the version that drives client refreshes."""
    repo = fixture_repository(tmp_path, with_report=True)
    before = snapshot_version(repo)

    write_completed_report(repo, passed=32, failed=2)

    assert snapshot_version(repo) != before


@pytest.mark.parametrize(
    "relative_path",
    [
        Path("tests/specs/smoke.spec.ts"),
        Path("requirements/smoke.md"),
        Path("playwright.config.ts"),
    ],
)
def test_source_deletion_marks_the_latest_report_stale(relative_path, tmp_path):
    """Removing covered source invalidates the report that described it."""
    repo = fixture_repository(tmp_path, with_report=True)

    (repo / relative_path).unlink()

    assert build_snapshot(repo)["targets"][0]["latest_run"]["state"] == "stale"


def test_copying_an_old_report_later_does_not_make_it_current(tmp_path):
    """Producer provenance wins over the destination report's modification time."""
    repo = fixture_repository(tmp_path, with_report=True)
    old_report = (repo / "reports" / "last-run.json").read_bytes()
    (repo / "tests" / "specs" / "smoke.spec.ts").write_text(
        "test('changed smoke', () => {});\n", encoding="utf-8"
    )

    (repo / "reports" / "last-run.json").write_bytes(old_report)

    assert build_snapshot(repo)["targets"][0]["latest_run"]["state"] == "stale"


def test_producer_and_dashboard_compute_the_same_source_provenance(tmp_path):
    """The Playwright producer and Python consumer share one fingerprint contract."""
    repo = fixture_repository(tmp_path, with_report=False)
    module_url = (
        Path(__file__).resolve().parents[1] / "testah_source_provenance.mjs"
    ).as_uri()
    script = (
        f"import {{ sourceProvenance }} from {json.dumps(module_url)}; "
        "console.log(JSON.stringify(sourceProvenance(process.argv[1])))"
    )

    producer = subprocess.run(
        ["node", "--input-type=module", "--eval", script, str(repo)],
        check=True,
        text=True,
        capture_output=True,
    )

    assert json.loads(producer.stdout) == source_provenance(repo)
