from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[2]


def test_ci_runs_on_staging_and_exercises_the_dashboard_when_present():
    workflow = (ROOT / ".github/workflows/tests.yml").read_text()

    assert "branches: [master, staging]" in workflow
    assert "\n  dashboard:\n" in workflow
    assert "pnpm dashboard:typecheck" in workflow
    assert "pnpm test:dashboard" in workflow
    assert "dashboard.playwright.config.ts" in workflow


def test_template_sync_includes_generic_dashboard_files_only():
    workflow = (ROOT / ".github/workflows/template-sync.yml").read_text()
    sync_script = (ROOT / "scripts/sync_template_paths.sh").read_text()

    assert "bash scripts/sync_template_paths.sh origin/master" in workflow
    assert "git rm -r --ignore-unmatch" in sync_script
    assert "git cat-file -e" in sync_script

    for path in (
        "dashboard/server.py",
        "dashboard/e2e/current-snapshot.spec.ts",
        "dashboard.playwright.config.ts",
        "tsconfig.dashboard.json",
        "tests/pages/CurrentSnapshotPage.ts",
        "requirements/dashboard/current-snapshot/overview.md",
        "page-maps/dashboard/current-snapshot/page.json",
    ):
        assert path in sync_script

    assert '"dashboard"' not in sync_script
    assert '"page-maps"' not in sync_script
    assert '"requirements"' not in sync_script


def test_template_sync_propagates_deletions_without_copying_project_data(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "--initial-branch=master")
    _git(repo, "config", "user.name", "Workflow Test")
    _git(repo, "config", "user.email", "workflow@example.test")

    _write(repo, "agents/guide.md", "old framework\n")
    _write(repo, "dashboard/e2e/current-snapshot.spec.ts", "stale test\n")
    _write(repo, "targets.yaml", "template-placeholder\n")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "template base")
    _git(repo, "branch", "template")

    _write(repo, "agents/guide.md", "new framework\n")
    _write(repo, "dashboard/server.py", "generic dashboard\n")
    (repo / "dashboard/e2e/current-snapshot.spec.ts").unlink()
    _write(repo, "dashboard/e2e/project-only.spec.ts", "project fixture\n")
    _write(repo, "targets.yaml", "project-specific\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", "master framework update")
    _git(repo, "switch", "template")

    subprocess.run(
        ["bash", str(ROOT / "scripts/sync_template_paths.sh"), "master"],
        cwd=repo,
        check=True,
    )

    assert (repo / "agents/guide.md").read_text() == "new framework\n"
    assert (repo / "dashboard/server.py").read_text() == "generic dashboard\n"
    assert not (repo / "dashboard/e2e/current-snapshot.spec.ts").exists()
    assert not (repo / "dashboard/e2e/project-only.spec.ts").exists()
    assert (repo / "targets.yaml").read_text() == "template-placeholder\n"


def test_template_allowlist_contains_no_project_brand_content():
    sync_script = (ROOT / "scripts/sync_template_paths.sh").read_text()
    manifest = sync_script.split("framework_paths=(", 1)[1].split("\n)", 1)[0]
    allowlisted_paths = [
        line.strip().strip('"') for line in manifest.splitlines() if line.strip()
    ]
    tracked_files = _git_output(ROOT, "ls-files", "--", *allowlisted_paths).splitlines()

    leaking_files = []
    for relative_path in tracked_files:
        contents = (ROOT / relative_path).read_text(errors="ignore")
        if "vi" + "zaeo" in contents.lower():
            leaking_files.append(relative_path)

    assert leaking_files == []


def _write(repo: Path, relative_path: str, contents: str) -> None:
    path = repo / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(contents)


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)


def _git_output(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=repo, check=True, capture_output=True, text=True
    ).stdout
