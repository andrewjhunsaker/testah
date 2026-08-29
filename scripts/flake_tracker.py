"""Track flaky tests across runs from Playwright JSON reports.

Usage: uv run python scripts/flake_tracker.py reports/last-run.json <run-id>
Updates flake-history.json and prints tests at/over the threshold
(3 flaky results in the last 10 runs), one per line.
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
                outcomes.append(
                    {"id": " > ".join(path + [spec["title"]]), "status": t.get("status")}
                )
        for child in suite.get("suites", []):
            walk(child, path + [child["title"]])

    for suite in report.get("suites", []):
        walk(suite, [suite["title"]])
    return outcomes


def update_history(history: dict, run_id: str, outcomes: list[dict]) -> dict:
    for o in outcomes:
        runs = history.setdefault(o["id"], [])
        runs.append({"run": run_id, "flaky": o["status"] == "flaky"})
        del runs[:-WINDOW]
    return history


def over_threshold(history: dict) -> list[str]:
    return [
        tid
        for tid, runs in history.items()
        if sum(r["flaky"] for r in runs[-WINDOW:]) >= THRESHOLD
    ]


if __name__ == "__main__":
    report = json.loads(Path(sys.argv[1]).read_text())
    history = json.loads(HISTORY_PATH.read_text()) if HISTORY_PATH.exists() else {}
    update_history(history, sys.argv[2], extract_outcomes(report))
    HISTORY_PATH.write_text(json.dumps(history, indent=2) + "\n")
    print("\n".join(over_threshold(history)))
