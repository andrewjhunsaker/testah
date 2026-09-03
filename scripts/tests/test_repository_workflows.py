from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[2]


def test_ci_runs_once_on_pull_requests_into_staging():
    workflow = (ROOT / ".github/workflows/tests.yml").read_text()

    assert "pull_request:\n    branches: [staging]" in workflow
    assert "\n  push:" not in workflow
    assert "\n  dashboard:\n" in workflow
    assert "pnpm dashboard:typecheck" in workflow
    assert "pnpm test:dashboard" in workflow
    assert "dashboard.playwright.config.ts" in workflow


def test_template_sync_uses_a_versioned_exact_file_manifest():
    workflow = (ROOT / ".github/workflows/template-sync.yml").read_text()
    sync_script = (ROOT / "scripts/sync_template_paths.sh").read_text()

    assert "bash scripts/sync_template_paths.sh origin/master" in workflow
    assert "git rm -f --ignore-unmatch" in sync_script
    assert "git cat-file -e" in sync_script
    assert 'HEAD:${manifest_path}' in sync_script

    for path in (
        "AGENTS.md",
        "docs/agents/issue-tracker.md",
        "docs/agents/triage-labels.md",
        "docs/agents/domain.md",
        "scripts/bootstrap_release_branches.sh",
        "scripts/sync_template_paths.sh",
        "scripts/template_paths.txt",
    ):
        assert path in _allowlisted_paths()

    for broad_directory in (
        "agents",
        "scripts",
        ".github",
        ".claude",
        "dashboard",
        "page-maps",
        "requirements",
    ):
        assert broad_directory not in _allowlisted_paths()


def test_every_template_manifest_entry_exists_as_a_file():
    missing_paths = [
        relative_path
        for relative_path in _allowlisted_paths()
        if not (ROOT / relative_path).is_file()
    ]

    assert missing_paths == []


def test_agent_harness_requires_staged_human_gated_delivery():
    agents = (ROOT / "AGENTS.md").read_text()
    claude = (ROOT / "CLAUDE.md").read_text()
    operating_procedure = (ROOT / "docs/running-the-loop.md").read_text()

    for contents in (agents, claude):
        assert "Never push directly to `master`" in contents
        assert "feature branch" in contents
        assert "`staging`" in contents
        assert "human" in contents.lower()

    assert "## Code Review Rules" in agents
    assert "@codex review" in agents
    assert "one Codex review gate" in agents
    assert "follow-up review" in agents
    normalized_procedure = " ".join(operating_procedure.split())
    assert "does not rerun CI or request another Codex review" in normalized_procedure


def test_template_issue_tracker_instructions_resolve_repo_from_git_remote():
    claude = (ROOT / "CLAUDE.md").read_text()
    tracker_guide = (ROOT / "docs/agents/issue-tracker.md").read_text()

    assert "andrewjhunsaker/testah" not in claude
    assert "andrewjhunsaker/testah" not in tracker_guide
    assert "git remote" in tracker_guide

    leaking_docs = []
    for relative_path in _allowlisted_paths():
        path = ROOT / relative_path
        if path.suffix == ".md" and path.is_file():
            if "andrewjhunsaker/testah" in path.read_text(errors="ignore"):
                leaking_docs.append(relative_path)
    assert leaking_docs == []


def test_template_sync_propagates_deletions_without_copying_project_data(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "--initial-branch=master")
    _git(repo, "config", "user.name", "Workflow Test")
    _git(repo, "config", "user.email", "workflow@example.test")

    _write(repo, "agents/scout.md", "old framework\n")
    _write(repo, "agents/retired.md", "retired framework\n")
    _write(repo, "dashboard/e2e/current-snapshot.spec.ts", "stale test\n")
    _write(repo, "scripts/sync_template_paths.sh", "old sync helper\n")
    _write(
        repo,
        "scripts/template_paths.txt",
        "agents/retired.md\nagents/scout.md\ndashboard/e2e/current-snapshot.spec.ts\n"
        "dashboard/server.py\nscripts/sync_template_paths.sh\n"
        "scripts/template_paths.txt\n",
    )
    _write(repo, "targets.yaml", "template-placeholder\n")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "template base")
    _git(repo, "branch", "template")

    _write(repo, "agents/scout.md", "new framework\n")
    _write(repo, "agents/project-only.md", "project-specific agent\n")
    _write(repo, "dashboard/server.py", "generic dashboard\n")
    _write(repo, "scripts/sync_template_paths.sh", "new sync helper\n")
    (repo / "agents/retired.md").unlink()
    (repo / "dashboard/e2e/current-snapshot.spec.ts").unlink()
    _write(repo, "dashboard/e2e/project-only.spec.ts", "project fixture\n")
    _write(
        repo,
        "scripts/template_paths.txt",
        "agents/scout.md\ndashboard/server.py\nscripts/sync_template_paths.sh\n"
        "scripts/template_paths.txt\n",
    )
    _write(repo, "targets.yaml", "project-specific\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", "master framework update")
    _git(repo, "switch", "template")
    _git(repo, "checkout", "master", "--", "scripts/sync_template_paths.sh")

    subprocess.run(
        ["bash", str(ROOT / "scripts/sync_template_paths.sh"), "master"],
        cwd=repo,
        check=True,
    )

    assert (repo / "agents/scout.md").read_text() == "new framework\n"
    assert not (repo / "agents/retired.md").exists()
    assert not (repo / "agents/project-only.md").exists()
    assert (repo / "dashboard/server.py").read_text() == "generic dashboard\n"
    assert (repo / "scripts/sync_template_paths.sh").read_text() == "new sync helper\n"
    assert not (repo / "dashboard/e2e/current-snapshot.spec.ts").exists()
    assert not (repo / "dashboard/e2e/project-only.spec.ts").exists()
    assert (repo / "targets.yaml").read_text() == "template-placeholder\n"


def test_template_allowlist_contains_no_project_brand_content():
    allowlisted_paths = _allowlisted_paths()
    tracked_files = _git_output(ROOT, "ls-files", "--", *allowlisted_paths).splitlines()

    leaking_files = []
    for relative_path in tracked_files:
        contents = (ROOT / relative_path).read_text(errors="ignore")
        if "vi" + "zaeo" in contents.lower():
            leaking_files.append(relative_path)

    assert leaking_files == []


def _allowlisted_paths() -> list[str]:
    return [
        line
        for line in (ROOT / "scripts/template_paths.txt").read_text().splitlines()
        if line and not line.startswith("#")
    ]


def test_release_branch_bootstrap_creates_staging_from_existing_master(tmp_path):
    remote = tmp_path / "remote.git"
    repo = tmp_path / "repo"
    _git(tmp_path, "init", "--bare", str(remote))
    repo.mkdir()
    _git(repo, "init", "--initial-branch=template")
    _git(repo, "config", "user.name", "Workflow Test")
    _git(repo, "config", "user.email", "workflow@example.test")
    _write(repo, "README.md", "starter\n")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "template base")
    _git(repo, "remote", "add", "origin", str(remote))
    _git(repo, "push", "origin", "template")
    # Simulate the human-controlled, one-time initialization required before setup.
    _git(repo, "push", "origin", "HEAD:master")

    subprocess.run(
        ["bash", str(ROOT / "scripts/bootstrap_release_branches.sh")],
        cwd=repo,
        check=True,
    )

    branches = _git_output(repo, "ls-remote", "--heads", "origin")
    assert "refs/heads/master" in branches
    assert "refs/heads/staging" in branches
    bootstrap = (ROOT / "scripts/bootstrap_release_branches.sh").read_text()
    assert 'git push origin "refs/heads/${release_branch}' not in bootstrap
    assert "bash scripts/bootstrap_release_branches.sh" in (
        ROOT / "setup.sh"
    ).read_text()
    setup = (ROOT / "setup.sh").read_text()
    assert "Use this as the project remote?" in setup
    assert "git remote set-url origin" in setup


def test_release_branch_bootstrap_refuses_to_create_master(tmp_path):
    remote = tmp_path / "remote.git"
    repo = tmp_path / "repo"
    _git(tmp_path, "init", "--bare", str(remote))
    repo.mkdir()
    _git(repo, "init", "--initial-branch=template")
    _git(repo, "config", "user.name", "Workflow Test")
    _git(repo, "config", "user.email", "workflow@example.test")
    _write(repo, "README.md", "starter\n")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "template base")
    _git(repo, "remote", "add", "origin", str(remote))
    _git(repo, "push", "origin", "template")

    result = subprocess.run(
        ["bash", str(ROOT / "scripts/bootstrap_release_branches.sh")],
        cwd=repo,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "human-initialized master" in result.stderr
    branches = _git_output(repo, "ls-remote", "--heads", "origin")
    assert "refs/heads/master" not in branches
    assert "refs/heads/staging" not in branches


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
