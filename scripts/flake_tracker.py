"""Track flaky tests across runs from Playwright JSON reports.

Usage: uv run python scripts/flake_tracker.py reports/last-run.json <run-id>
Updates flake-history.json and prints tests at/over the threshold
(3 flaky results in the last 10 runs), one per line. Only tests present in
the given report are printed, so deleted tests never resurface.
"""

import json
import sys
from pathlib import Path

WINDOW = 10
THRESHOLD = 3
HISTORY_PATH = Path("flake-history.json")


def extract_outcomes(report: dict) -> list[dict]:
    outcomes: list[dict] = []

    def walk(suite: dict, path: list[str]) -> None:
        for spec in suite.get("specs", []):
            for t in spec.get("tests", []):
                parts = path + [spec["title"]]
                if t.get("projectName"):
                    parts.append(t["projectName"])
                outcomes.append({"id": " > ".join(parts), "status": t.get("status")})
        for child in suite.get("suites", []):
            walk(child, path + [child["title"]])

    for suite in report.get("suites", []):
        walk(suite, [suite["title"]])
    return outcomes


def update_history(history: dict, run_id: str, outcomes: list[dict]) -> dict:
    for o in outcomes:
        runs = history.setdefault(o["id"], [])
        if runs and runs[-1]["run"] == run_id:
            continue  # idempotent: reprocessing a report must not double-count
        runs.append({"run": run_id, "flaky": o["status"] == "flaky"})
        del runs[:-WINDOW]
    return history


def over_threshold(history: dict, active_ids: set | None = None) -> list[str]:
    return [
        tid
        for tid, runs in history.items()
        if (active_ids is None or tid in active_ids)
        and sum(r["flaky"] for r in runs[-WINDOW:]) >= THRESHOLD
    ]


if __name__ == "__main__":
    report = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    history = (
        json.loads(HISTORY_PATH.read_text(encoding="utf-8"))
        if HISTORY_PATH.exists()
        else {}
    )
    outcomes = extract_outcomes(report)
    update_history(history, sys.argv[2], outcomes)
    HISTORY_PATH.write_text(json.dumps(history, indent=2) + "\n", encoding="utf-8")
    print("\n".join(over_threshold(history, {o["id"] for o in outcomes})))
