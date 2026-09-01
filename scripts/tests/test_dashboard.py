import json
import os
import subprocess
import threading
from contextlib import contextmanager
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from dashboard.server import make_server
from dashboard.snapshot import snapshot_version


COMPLETED_REPORT = {
    "config": {
        "projects": [
            {"use": {"baseURL": "https://staging.vizaeo.com"}},
        ],
    },
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
    report = {
        **COMPLETED_REPORT,
        "stats": {
            **COMPLETED_REPORT["stats"],
            "expected": passed,
            "unexpected": failed,
        },
    }
    (repo / "reports" / "last-run.json").write_text(json.dumps(report), encoding="utf-8")


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
  vizaeo:
    name: Vizaeo
    base_url: https://staging.vizaeo.com
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
    playwright_config = repo / "playwright.config.ts"
    if report_case == "older-than-playwright-config":
        playwright_config.write_text("export default {};\n", encoding="utf-8")
    if with_report:
        (repo / "reports").mkdir()
        report_path = repo / "reports" / "last-run.json"
        if report_case == "malformed":
            report_path.write_text("not json", encoding="utf-8")
        else:
            report = COMPLETED_REPORT
            if report_case == "incomplete":
                report = {"stats": {"expected": 33}}
            elif report_case == "unattributed":
                report = {
                    **COMPLETED_REPORT,
                    "config": {"projects": [{"use": {"baseURL": "https://unknown.example"}}]},
                }
            report_path.write_text(json.dumps(report), encoding="utf-8")
            if report_case == "older-than-sources":
                source_path = repo / "tests" / "specs" / "smoke.spec.ts"
                newer_time = report_path.stat().st_mtime + 1
                os.utime(source_path, (newer_time, newer_time))
            if report_case == "older-than-playwright-config":
                newer_time = report_path.stat().st_mtime + 1
                os.utime(playwright_config, (newer_time, newer_time))
    subprocess.run(["git", "init", "-b", "master"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Fixture User"], cwd=repo, check=True)
    subprocess.run(
        ["git", "config", "user.email", "fixture@example.com"], cwd=repo, check=True
    )
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "fixture"], cwd=repo, check=True)
    return repo


@contextmanager
def running_dashboard(repo: Path):
    server = make_server(repo)
    thread = threading.Thread(target=server.serve_forever)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        thread.join()
        server.server_close()


def get_json(url: str) -> dict:
    with urlopen(url) as response:
        return json.loads(response.read())


def test_current_snapshot_is_served_from_a_fixture_repository(tmp_path):
    """A configured report is exposed as its normalized HTTP snapshot."""
    repo = fixture_repository(tmp_path, with_report=True)

    with running_dashboard(repo) as base_url:
        snapshot = get_json(f"{base_url}/api/snapshot")

    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, check=True, text=True, capture_output=True
    ).stdout.strip()
    assert snapshot["repository"] == {"branch": "master", "commit": commit}
    assert snapshot["targets"] == [
        {
            "key": "vizaeo",
            "name": "Vizaeo",
            "base_url": "https://staging.vizaeo.com",
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
    """Non-standard JSON numbers make the report unavailable at the HTTP seam."""
    repo = fixture_repository(tmp_path, with_report=True)
    report_path = repo / "reports" / "last-run.json"
    report = json.dumps(COMPLETED_REPORT).replace("14404.824", constant, 1)
    report_path.write_text(report, encoding="utf-8")

    with running_dashboard(repo) as base_url:
        target = get_json(f"{base_url}/api/snapshot")["targets"][0]

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
        **COMPLETED_REPORT,
        "stats": {**COMPLETED_REPORT["stats"], field: value},
    }
    (repo / "reports" / "last-run.json").write_text(
        json.dumps(report), encoding="utf-8"
    )

    with running_dashboard(repo) as base_url:
        latest_run = get_json(f"{base_url}/api/snapshot")["targets"][0]["latest_run"]

    assert latest_run["state"] == "incomplete"
    if field == "expected":
        assert latest_run["counts"]["passed"] is None
    elif field == "duration":
        assert latest_run["duration_ms"] is None
    else:
        assert latest_run["started_at"] is None


def test_snapshot_normalizes_iso_start_time(tmp_path):
    """A valid report timestamp is returned as a normalized UTC ISO timestamp."""
    repo = fixture_repository(tmp_path, with_report=True)
    report = {
        **COMPLETED_REPORT,
        "stats": {
            **COMPLETED_REPORT["stats"],
            "startTime": "2026-08-28T19:11:39.230+02:00",
        },
    }
    (repo / "reports" / "last-run.json").write_text(
        json.dumps(report), encoding="utf-8"
    )

    with running_dashboard(repo) as base_url:
        latest_run = get_json(f"{base_url}/api/snapshot")["targets"][0]["latest_run"]

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

    with running_dashboard(repo) as base_url:
        target = get_json(f"{base_url}/api/snapshot")["targets"][0]

    assert target["latest_run"]["state"] == expected_state


def test_dashboard_rejects_mutation_requests(tmp_path):
    """The public dashboard interface accepts no mutation request."""
    repo = fixture_repository(tmp_path, with_report=True)

    with running_dashboard(repo) as base_url:
        with pytest.raises(HTTPError) as error:
            urlopen(Request(f"{base_url}/api/snapshot", method="POST"))

    assert error.value.code == 405


def test_snapshot_response_is_not_cacheable(tmp_path):
    """An operator always reads fresh local repository evidence."""
    repo = fixture_repository(tmp_path, with_report=True)

    with running_dashboard(repo) as base_url:
        with urlopen(f"{base_url}/api/snapshot") as response:
            assert response.headers["Cache-Control"] == "no-store"


def test_snapshot_version_is_served_from_the_fixture_repository(tmp_path):
    """The lightweight version endpoint fingerprints the repository evidence."""
    repo = fixture_repository(tmp_path, with_report=True)

    with running_dashboard(repo) as base_url:
        version = get_json(f"{base_url}/api/version")

    assert version == {"version": snapshot_version(repo)}


def test_snapshot_version_changes_with_dashboard_evidence(tmp_path):
    """A report rewrite changes the version that drives client refreshes."""
    repo = fixture_repository(tmp_path, with_report=True)
    before = snapshot_version(repo)

    write_completed_report(repo, passed=32, failed=2)

    assert snapshot_version(repo) != before
