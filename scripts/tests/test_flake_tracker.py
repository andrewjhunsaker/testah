from scripts.flake_tracker import extract_outcomes, over_threshold, update_history

REPORT = {
    "suites": [
        {
            "title": "smoke.spec.ts",
            "specs": [
                {"title": "home page loads", "tests": [{"status": "flaky"}]},
                {"title": "help renders", "tests": [{"status": "expected"}]},
            ],
            "suites": [
                {
                    "title": "nested",
                    "specs": [
                        {"title": "deep test", "tests": [{"status": "unexpected"}]}
                    ],
                }
            ],
        }
    ]
}


def test_extract_outcomes_flattens_nested_suites():
    outcomes = extract_outcomes(REPORT)
    assert {"id": "smoke.spec.ts > home page loads", "status": "flaky"} in outcomes
    assert {"id": "smoke.spec.ts > nested > deep test", "status": "unexpected"} in outcomes
    assert len(outcomes) == 3


def test_threshold_is_3_flaky_of_last_10():
    history = {}
    for i in range(2):
        update_history(history, f"run{i}", [{"id": "t1", "status": "flaky"}])
    assert over_threshold(history) == []
    update_history(history, "run2", [{"id": "t1", "status": "flaky"}])
    assert over_threshold(history) == ["t1"]


def test_history_window_caps_at_10_runs():
    history = {}
    for i in range(3):
        update_history(history, f"flaky{i}", [{"id": "t1", "status": "flaky"}])
    for i in range(10):
        update_history(history, f"ok{i}", [{"id": "t1", "status": "expected"}])
    assert len(history["t1"]) == 10
    assert over_threshold(history) == []


def test_multi_project_outcomes_get_distinct_ids():
    report = {
        "suites": [
            {
                "title": "smoke.spec.ts",
                "specs": [
                    {
                        "title": "home page loads",
                        "tests": [
                            {"status": "flaky", "projectName": "chromium"},
                            {"status": "expected", "projectName": "firefox"},
                        ],
                    }
                ],
            }
        ]
    }
    outcomes = extract_outcomes(report)
    assert {
        "id": "smoke.spec.ts > home page loads > chromium",
        "status": "flaky",
    } in outcomes
    assert {
        "id": "smoke.spec.ts > home page loads > firefox",
        "status": "expected",
    } in outcomes


def test_update_history_is_idempotent_per_run():
    history = {}
    for _ in range(3):
        update_history(history, "run1", [{"id": "t1", "status": "flaky"}])
    assert len(history["t1"]) == 1


def test_over_threshold_ignores_tests_absent_from_current_run():
    history = {}
    for i in range(3):
        update_history(history, f"run{i}", [{"id": "gone", "status": "flaky"}])
    assert over_threshold(history) == ["gone"]
    assert over_threshold(history, active_ids={"still-here"}) == []
