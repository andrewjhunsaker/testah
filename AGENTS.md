# Testah agent policy

These rules apply to every agent and automation working in this repository.

## Delivery workflow

- Make changes on a feature branch and open a pull request into `staging`.
- Never push directly to `master`. Never merge a pull request into `master`.
- Wait for the staging PR's required CI jobs to pass.
- Use one Codex review gate on each staging PR: request `@codex review` after
  CI passes. Address consequential findings and request a follow-up review only
  when the reviewed commit must change. Merge only after the current commit is
  clean.
- Each merge to `staging` makes GitHub Actions open or update a bot-authored
  draft promotion PR into `master`. After local validation, an agent may mark
  that PR ready and must stop. A human must approve and merge it.
- Do not rerun CI or request another Codex review on the promotion PR. Its
  contents were already gated on their staging PRs.
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
