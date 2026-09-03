# Testah agent policy

These rules apply to every agent and automation working in this repository.

## Delivery workflow

- Make changes on a feature branch and open a pull request into `staging`.
- Never push directly to `master`. Never merge a pull request into `master`.
- Wait for the staging PR's required CI jobs to pass.
- Use one Codex review gate on each staging PR: request `@codex review` after
  CI passes. Address consequential findings and request a follow-up review only
  when the reviewed commit must change. The required `codex-review` status
  verifies that the exact head SHA has a review with no inline findings. Merge
  only after that status passes.
- Each merge to `staging` makes GitHub Actions open or update a bot-authored
  draft promotion PR into `master`; a new staging commit returns an existing
  ready promotion to draft. The staging-push workflow publishes a
  `promotion-source` check on that PR's unique test-merge commit because GitHub
  does not automatically run the trusted target workflow for a PR created with
  `GITHUB_TOKEN`; the master-target gate publishes a failing PR-specific check
  for every other source. After local validation, an agent may mark that PR
  ready and must stop. A human must approve the latest staging head and merge
  it; new staging commits dismiss the prior approval. Do not require a different
  last-push approver: agent staging merges use the human owner's GitHub identity,
  and stale-review dismissal already refreshes the gate.
- Do not rerun CI or request another Codex review on the promotion PR. Its
  contents were already gated on their staging PRs.
- One-time migration exception: an existing repository's first PR introducing
  the trusted `codex-review` workflow cannot emit that status until the workflow
  reaches the default branch. Manually verify the exact-head Codex review for
  that staging PR. The staging-push workflow emits `promotion-source` for the
  first promotion without an exception. No exception exists after the gate
  workflow is on `master`; repositories initialized from `template` already
  contain it.
- A merge to `master` is the release event. Let the template-sync workflow copy
  its exact allowlist of project-agnostic framework files to `template`; never
  copy target-specific project data there.

GitHub branch protection is the mechanical enforcement layer. These
instructions remain defense-in-depth and define who may perform each action.

## Code Review Rules

- Prioritize correctness, security, data loss, broken workflow gates, and
  regressions over stylistic preferences.
- Verify that CI runs on PRs targeting `staging`, and is not duplicated for the
  `staging` to `master` promotion.
- Treat any direct-push path to `master`, automated master merge, or branch
  protection bypass as a blocking finding.
- For template-bound changes, verify every synced path is project-agnostic and
  explicitly allowlisted. Flag target names, credentials, private artifacts,
  and broad directory copies.
- Report only actionable findings introduced by the PR, with file and line
  references when possible.
