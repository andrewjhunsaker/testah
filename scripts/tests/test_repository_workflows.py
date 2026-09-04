from pathlib import Path
import json
import os
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
    assert "github.event.pull_request.base.sha" in workflow
    assert "dashboard config was removed" in workflow


def test_playwright_report_persists_the_effective_target_url(tmp_path):
    config_path = tmp_path / "playwright.config.ts"
    config_path.write_text(
        (ROOT / "playwright.config.ts").read_text(), encoding="utf-8"
    )
    subprocess.run(
        [
            "node",
            str(ROOT / "scripts" / "configure_playwright_target.mjs"),
            "https://configured.example.test",
            str(config_path),
        ],
        check=True,
    )
    config = config_path.read_text(encoding="utf-8")

    assert "const testahBaseURL =" in config
    assert "metadata:" in config
    assert "sourceProvenance" in config
    assert "testahBaseURL" in config
    assert "use: {" in config
    assert config.count("baseURL: testahBaseURL") == 2
    assert "https://configured.example.test" in config


def test_setup_adds_report_metadata_to_the_template_playwright_config(tmp_path):
    config_path = tmp_path / "playwright.config.ts"
    config_path.write_text(
        "import { defineConfig } from '@playwright/test'\n\n"
        "export default defineConfig({\n"
        "  use: {\n"
        "    baseURL: process.env.TESTAH_BASE_URL ?? 'https://example.test',\n"
        "  },\n"
        "})\n",
        encoding="utf-8",
    )
    helper = ROOT / "scripts" / "configure_playwright_target.mjs"

    subprocess.run(
        ["node", str(helper), "https://new.example.test/it's", str(config_path)],
        check=True,
    )
    subprocess.run(
        ["node", str(helper), "https://newer.example.test", str(config_path)],
        check=True,
    )

    configured = config_path.read_text(encoding="utf-8")
    assert (
        "process.env.TESTAH_BASE_URL ?? 'https://newer.example.test'\n\n"
        "const testahSourceProvenance = sourceProvenance()"
    ) in configured
    assert "it\\'s" not in configured
    assert configured.count("const testahBaseURL =") == 1
    assert configured.count("metadata:") == 1
    assert configured.count("baseURL: testahBaseURL") == 2
    assert configured.count("...testahSourceProvenance,") == 1


def test_setup_uses_the_synced_playwright_metadata_helper():
    setup = (ROOT / "setup.sh").read_text()

    assert "node scripts/configure_playwright_target.mjs" in setup
    assert "s|process.env.TESTAH_BASE_URL" not in setup
    assert "scripts/configure_playwright_target.mjs" in _allowlisted_paths()
    assert "scripts/testah_source_provenance.mjs" in _allowlisted_paths()


def test_codex_review_gate_runs_only_trusted_workflow_code():
    workflow = (ROOT / ".github/workflows/codex-review.yml").read_text()

    assert "pull_request_target:" in workflow
    assert "pull_request_review:" in workflow
    assert "issue_comment:" in workflow
    assert "types: [created, edited]" in workflow
    assert "types: [submitted]" in workflow
    assert "branches: [staging, master]" in workflow
    assert "pull_request_review:\n    types: [submitted]" in workflow
    assert "\n  codex-review:\n" in workflow
    assert "actions/checkout" not in workflow
    assert "statuses: write" in workflow
    assert "github.event.pull_request.head.sha" in workflow
    assert "github.event.review.commit_id" in workflow
    assert "github.event.review.id" in workflow
    assert "chatgpt-codex-connector[bot]" in workflow
    assert "github.event.pull_request.base.ref == 'staging'" in workflow
    assert "github.event.comment.user.login" in workflow
    assert "Codex Review: Didn't find any major issues." in workflow
    assert "Reviewed commit:" in workflow
    assert "commits/${REVIEWED_PREFIX}" in workflow
    assert '"$RESOLVED_SHA" != "$HEAD_SHA"' in workflow
    assert "issues/${PR_NUMBER}/comments?per_page=100" in workflow
    assert workflow.index("-f state=pending") < workflow.index(
        "issues/${PR_NUMBER}/comments?per_page=100"
    )
    assert "pull_request_review_id" in workflow
    assert "statuses/${HEAD_SHA}" in workflow
    assert "state=pending" in workflow
    assert "state=success" in workflow
    assert "state=failure" in workflow
    assert workflow.count("--paginate --slurp | jq") == 3
    assert "pulls/${PR_NUMBER}/reviews?per_page=100" in workflow
    assert 'select(.user.login == $codex_login and .commit_id == $head_sha)' in workflow
    assert "| last | .id // empty" in workflow
    assert workflow.index("-f state=pending") < workflow.index(
        "pulls/${PR_NUMBER}/reviews?per_page=100"
    )
    assert "--argjson review_id" in workflow


def test_master_pr_gate_accepts_only_same_repo_staging_promotions():
    workflow = (ROOT / ".github/workflows/codex-review.yml").read_text()

    assert "branches: [staging, master]" in workflow
    assert "\n  promotion-source:\n" in workflow
    assert "github.event.pull_request.base.ref == 'master'" in workflow
    assert "github.event.pull_request.head.repo.full_name" in workflow
    assert "github.event.pull_request.head.ref" in workflow
    assert "github.event.pull_request.user.login" in workflow
    assert "github.event.pull_request.merge_commit_sha" in workflow
    assert '"$HEAD_REPOSITORY" = "$REPOSITORY"' in workflow
    assert '"$HEAD_BRANCH" = "staging"' in workflow
    assert '"$AUTHOR_LOGIN" = "github-actions[bot]"' in workflow
    assert "checks: write" in workflow
    assert "check-runs" in workflow
    assert 'head_sha="$MERGE_SHA"' in workflow
    assert "name=promotion-source" in workflow
    assert "conclusion=success" in workflow
    assert "conclusion=failure" in workflow


def test_staging_push_opens_a_bot_authored_draft_promotion_pr():
    workflow = (ROOT / ".github/workflows/promotion-pr.yml").read_text()

    assert "push:\n    branches: [staging]" in workflow
    assert "pull-requests: write" in workflow
    assert "checks: write" in workflow
    assert "github.sha" in workflow
    assert "pulls/${number}" in workflow
    assert ".merge_commit_sha" in workflow
    assert "check-runs" in workflow
    assert 'head_sha="$merge_sha"' in workflow
    assert "name=promotion-source" in workflow
    assert "conclusion=success" in workflow
    assert "gh pr create" in workflow
    assert "--base master" in workflow
    assert "--head staging" in workflow
    assert "--draft" in workflow
    assert "head=${OWNER}:staging" in workflow
    assert "[.number, .draft]" in workflow
    assert '.user.login == "github-actions[bot]"' in workflow
    assert "non-bot staging promotion PR" in workflow
    assert "[0] // empty" in workflow
    assert "gh pr ready" in workflow
    assert "--undo" in workflow
    assert "@codex review" not in workflow
    assert "pytest" not in workflow
    assert "playwright" not in workflow


def test_template_sync_uses_a_versioned_exact_file_manifest():
    workflow = (ROOT / ".github/workflows/template-sync.yml").read_text()
    sync_script = (ROOT / "scripts/sync_template_paths.sh").read_text()

    assert "bash scripts/sync_template_paths.sh origin/master" in workflow
    assert "git rm -f --ignore-unmatch" in sync_script
    assert "git cat-file -e" in sync_script
    assert 'HEAD:${manifest_path}' in sync_script

    for path in (
        "AGENTS.md",
        "dashboard.playwright.config.ts",
        "dashboard/__init__.py",
        "dashboard/__main__.py",
        "dashboard/e2e/current-snapshot.spec.ts",
        "dashboard/server.py",
        "dashboard/snapshot.py",
        "dashboard/ui/app.ts",
        "dashboard/ui/index.html",
        "dashboard/ui/styles.css",
        "docs/agents/issue-tracker.md",
        "docs/agents/triage-labels.md",
        "docs/agents/domain.md",
        ".github/workflows/codex-review.yml",
        ".github/workflows/promotion-pr.yml",
        "scripts/bootstrap_github_labels.sh",
        "scripts/bootstrap_github_protections.sh",
        "scripts/bootstrap_release_branches.sh",
        "scripts/configure_playwright_target.mjs",
        "scripts/sync_template_paths.sh",
        "scripts/template_paths.txt",
        "scripts/testah_source_provenance.d.mts",
        "scripts/testah_source_provenance.mjs",
        "scripts/tests/test_dashboard.py",
        "tests/pages/CurrentSnapshotPage.ts",
        "requirements/dashboard/current-snapshot/overview.md",
        "page-maps/dashboard/current-snapshot/page.json",
        "tsconfig.dashboard.json",
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
    assert "One-time migration exception" in agents
    assert "No exception exists after" in agents
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


def test_template_requirements_have_self_contained_provenance():
    leaking_requirements = []
    for relative_path in _allowlisted_paths():
        if not relative_path.startswith("requirements/"):
            continue
        contents = (ROOT / relative_path).read_text()
        if "GitHub Issue #" in contents or "docs/adr/" in contents:
            leaking_requirements.append(relative_path)

    assert leaking_requirements == []


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
    assert "git config --replace-all remote.origin.fetch" in setup
    assert "+refs/heads/*:refs/remotes/origin/*" in setup
    assert "git fetch origin --prune" in setup
    assert "gh repo edit --default-branch master" in setup
    assert "defaultBranchRef" in setup
    assert "--enable-merge-commit" in setup
    assert "--enable-rebase-merge=false" in setup
    assert "--enable-squash-merge=false" in setup
    assert "mergeCommitAllowed" in setup
    assert "rebaseMergeAllowed" in setup
    assert "squashMergeAllowed" in setup
    normalized_setup = " ".join(setup.split())
    assert (
        'git remote set-url origin "$url" && git push -u origin "$branch"'
        in normalized_setup
    )
    assert "[github/skip]" in setup
    assert setup.count('[ "$branch" != template ]') == 2
    assert "Refusing to create a remote from $branch" in setup
    for project_setup_document in (
        setup,
        (ROOT / "README.md").read_text(),
        (ROOT / "docs/running-the-loop.md").read_text(),
    ):
        assert "gitlab" not in project_setup_document.lower()
        assert "bitbucket" not in project_setup_document.lower()


def test_setup_fetch_normalization_replaces_multiple_refspecs(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "--initial-branch=template")
    _git(repo, "remote", "add", "origin", "https://example.test/original.git")
    _git(
        repo,
        "config",
        "--add",
        "remote.origin.fetch",
        "+refs/pull/*/head:refs/remotes/origin/pull/*",
    )

    subprocess.run(
        [
            "git",
            "config",
            "--replace-all",
            "remote.origin.fetch",
            "+refs/heads/*:refs/remotes/origin/*",
        ],
        cwd=repo,
        check=True,
    )

    values = _git_output(repo, "config", "--get-all", "remote.origin.fetch")
    assert values.splitlines() == ["+refs/heads/*:refs/remotes/origin/*"]


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


def test_setup_provisions_canonical_github_triage_labels(tmp_path):
    setup = (ROOT / "setup.sh").read_text()
    label_bootstrap = (ROOT / "scripts/bootstrap_github_labels.sh").read_text()

    assert "bash scripts/bootstrap_github_labels.sh" in setup
    assert "--force" in label_bootstrap
    for label in (
        "needs-triage",
        "needs-info",
        "ready-for-agent",
        "ready-for-human",
        "wontfix",
    ):
        assert f"gh label create {label} " in label_bootstrap

    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_gh = fake_bin / "gh"
    fake_gh.write_text(
        '#!/usr/bin/env bash\nprintf \'%s\\n\' "$*" >> "$TESTAH_LABEL_LOG"\n'
    )
    fake_gh.chmod(0o755)
    label_log = tmp_path / "labels.log"
    env = os.environ | {
        "PATH": f"{fake_bin}:{os.environ['PATH']}",
        "TESTAH_LABEL_LOG": str(label_log),
    }

    subprocess.run(
        ["bash", str(ROOT / "scripts/bootstrap_github_labels.sh")],
        env=env,
        check=True,
    )

    calls = label_log.read_text().splitlines()
    assert len(calls) == 5
    assert all("label create" in call and "--force" in call for call in calls)


def test_setup_provisions_github_branch_protection(tmp_path):
    setup = (ROOT / "setup.sh").read_text()
    protection_bootstrap = (
        ROOT / "scripts/bootstrap_github_protections.sh"
    ).read_text()

    assert "bash scripts/bootstrap_github_protections.sh" in setup
    assert "repository is not ready" in setup
    assert "branches/staging/protection" in protection_bootstrap
    assert "branches/master/protection" in protection_bootstrap
    assert (
        '"checks":[{"context":"scripts-unit","app_id":${actions_app_id}}'
        in protection_bootstrap
    )
    assert '"context":"promotion-source","app_id":${actions_app_id}' in protection_bootstrap
    assert "apps/github-actions" in protection_bootstrap
    assert '"required_approving_review_count":1' in protection_bootstrap
    assert '"dismiss_stale_reviews":true' in protection_bootstrap
    assert '"require_last_push_approval":false' in protection_bootstrap
    assert "actions/permissions/workflow" in protection_bootstrap
    assert '"can_approve_pull_request_reviews":true' in protection_bootstrap
    assert protection_bootstrap.count('"enforce_admins":true') == 2
    assert protection_bootstrap.count('"required_linear_history":false') == 2
    assert protection_bootstrap.count('"required_conversation_resolution":true') == 2
    assert protection_bootstrap.count('"allow_force_pushes":false') == 2
    assert protection_bootstrap.count('"allow_deletions":false') == 2

    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_gh = fake_bin / "gh"
    fake_gh.write_text(
        "#!/usr/bin/env bash\n"
        'if [[ "$*" == *"apps/github-actions"* ]]; then\n'
        "  printf '15368\\n'\n"
        "  exit 0\n"
        "fi\n"
        'payload=$(cat)\n'
        'printf \'%s|%s\\n\' "$*" "$payload" >> "$TESTAH_PROTECTION_LOG"\n'
    )
    fake_gh.chmod(0o755)
    protection_log = tmp_path / "protections.log"
    env = os.environ | {
        "PATH": f"{fake_bin}:{os.environ['PATH']}",
        "TESTAH_PROTECTION_LOG": str(protection_log),
    }

    subprocess.run(
        ["bash", str(ROOT / "scripts/bootstrap_github_protections.sh")],
        env=env,
        check=True,
    )

    calls = protection_log.read_text().splitlines()
    assert len(calls) == 3
    staging_args, staging_payload_text = calls[0].split("|", 1)
    master_args, master_payload_text = calls[1].split("|", 1)
    actions_args, actions_payload_text = calls[2].split("|", 1)
    assert "--method PUT" in staging_args
    assert "branches/staging/protection" in staging_args
    assert "--method PUT" in master_args
    assert "branches/master/protection" in master_args
    assert "--method PUT" in actions_args
    assert "actions/permissions/workflow" in actions_args
    staging_payload = json.loads(staging_payload_text)
    master_payload = json.loads(master_payload_text)
    actions_payload = json.loads(actions_payload_text)
    assert staging_payload["required_status_checks"]["checks"] == [
        {"context": "scripts-unit", "app_id": 15368},
        {"context": "e2e", "app_id": 15368},
        {"context": "dashboard", "app_id": 15368},
        {"context": "codex-review", "app_id": 15368},
    ]
    assert master_payload["required_status_checks"] == {
        "strict": False,
        "checks": [{"context": "promotion-source", "app_id": 15368}],
    }
    assert master_payload["required_pull_request_reviews"][
        "required_approving_review_count"
    ] == 1
    assert master_payload["required_pull_request_reviews"][
        "dismiss_stale_reviews"
    ] is True
    assert master_payload["required_pull_request_reviews"][
        "require_last_push_approval"
    ] is False
    assert actions_payload == {
        "default_workflow_permissions": "read",
        "can_approve_pull_request_reviews": True,
    }
    for payload in (staging_payload, master_payload):
        assert payload["enforce_admins"] is True
        assert payload["required_pull_request_reviews"] is not None
        assert payload["required_linear_history"] is False
        assert payload["allow_force_pushes"] is False
        assert payload["allow_deletions"] is False
        assert payload["required_conversation_resolution"] is True


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
