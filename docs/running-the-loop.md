# Running the loop

How one iteration is actually executed. Design rationale lives in
[spec.md](spec.md); this file is the operating procedure.

An "agent pass" is a Claude Code session whose instructions are one file from
`agents/`. Nothing is scheduled and there is no daemon — a human starts each
pass, and the **repo is the message bus**: each pass reads the artifacts the
previous one committed, and its own commit is the notification to the next.
Run every command from the repo root.

## One iteration

| # | Pass | Started by | Reads | Writes |
|---|---|---|---|---|
| 1 | **Scout** — `agents/scout.md` | human, on demand | `targets.yaml`, existing `page-maps/` | `page-maps/<target>/<slug>/{page.md,page.json,features.md,perf.json,meta.json}`, `changed-pages.json`, `tickets/drafts/*.md` (`type: test-feature`) |
| 2 | **Author Mode A** — `agents/author.md` | human, after the Scout gate | page-maps, `changed-pages.json`, `RULES.md`, approved feature tickets | `requirements/<target>/<slug>/<feature>.md`, `tests/pages/*.ts`, `tests/specs/*.spec.ts` |
| 2R | **Reviewer** — `agents/reviewer.md` | the Author, as a **fresh subagent** | the Author's diff, `requirements/`, `RULES.md` | `reviews/<date>.md` (`-2`, `-3` for repeat rounds) |
| 3 | **Agentless run** — `pnpm exec playwright test` | CI on PRs into `staging`, or a human locally | `tests/`, `playwright.config.ts` | `reports/last-run.json`, `reports/html/` (both gitignored) |
| 4 | **Author Mode B** — `agents/author.md` | human, per run that produced failures | `reports/last-run.json`, traces, page-map history, git log | `triage/<run-id>.md`, `flake-history.json`, `docs/coverage/<target>.{html,md}` (regenerated) |
| 5 | **Steward** — `agents/steward.md` | human, after triage | triage, reviews, page-maps, `features.md`, drafts, `flake-history.json` | `tickets/drafts/*.md` (`product-bug` / `framework-update`), `critiques/<date>.md`, `docs/` |

Step 2R is not a peer pass: the Author spawns it in fresh context and re-spawns
until every row is `pass`. Reviewing inside the Author's own session is the
self-grading failure the role exists to prevent.

## Commands

    # Scout, per designated page
    uv run python scripts/crawl.py <base_url><path> page-maps/<target>/<slug>
    uv run python scripts/drift.py <target> <slug> <url>   # → new | changed | unchanged

    # Agentless run (no agent involved — this is the point)
    pnpm exec playwright test
    pnpm exec playwright test --grep @smoke
    TESTAH_BASE_URL=https://other.example pnpm exec playwright test

    # Author Mode B, before triage
    gh run download <run-id> -n playwright-report -D reports/   # CI runs only
    uv run python scripts/flake_tracker.py reports/last-run.json <run-id>
    # run-id = the CI run number, or local-<date>

    # Author Mode B, after triage — refresh the visual coverage map
    uv run python -m scripts.coverage_map

    # Framework's own tests
    uv run pytest -v

`scripts/flake_tracker.py` prints one line per test at or over **3 flaky
results in the last 10 runs**; silence means no crossing. It is idempotent —
reprocessing the same report under the same run-id does not double-count.

CI is `.github/workflows/tests.yml`: `scripts-unit` (pytest) and `e2e`
(Playwright, chromium), on pull requests targeting `staging` only.
When the generic dashboard is present, the separate `dashboard` job runs its
typecheck and loopback-browser suite. `e2e` uploads `reports/` as the
`playwright-report` artifact even on failure — that artifact is Mode B's input.

## Staging promotion

Feature and framework work must start on a feature branch and enter `staging`
through a PR. GitHub branch protection rejects direct pushes to `staging` and
requires the `scripts-unit`, `e2e`, and `dashboard` checks. Once those checks
pass, request `@codex review`; address consequential findings and request a
follow-up review when they require a new commit. The agent may merge the PR into
`staging` only after the current commit is clean.

After the combined branch has been exercised locally, open a promotion PR from
`staging` to `master` and stop. GitHub branch protection rejects direct pushes
to `master`, including administrator pushes, and requires the PR path. A human
must inspect and merge this promotion PR. It does not rerun CI or request
another Codex review: those gates already ran on the constituent staging PRs.

The merge to `master` is the validated release event. It triggers the
project-data-free `template` sync; that workflow copies only the exact paths in
`scripts/template_paths.txt`.

## Gates in PRODUCTION mode

Per [spec.md §11](spec.md). Each is a human stop, not a notification:

| Gate | Who | What |
|---|---|---|
| Page-map updates | Human | PR carrying the drift summary — never raw DOM |
| Acceptance criteria | Human | **ALWAYS ON — no run mode collapses it.** The Author writes criteria with frontmatter `approved: false` and stops; tests are generated only from criteria the human has flipped to `approved: true` |
| Test framework changes | Reviewer (floor) → Human (merge) | PR |
| All Linear tickets | Human flips `status: draft` → `approved`; the Steward then files and sets `status: filed:<id>` | `tickets/drafts/` |
| Critique adoption | Human | which recommendations become work |

Tickets file to whatever the top-level `tracker:` block in `targets.yaml`
configures (testah is tracker-agnostic; Linear via MCP is the reference
implementation) — including product bugs found in targets. A target with
`ticketing: direct` skips the draft step and files immediately; the example
configuration uses `draft`.

Agents never edit `RULES.md` or `targets.yaml`. Both are human-owned law.

## Current validation-mode deviations

The first iteration (`docs/plans/2026-08-28-testah-v1.md`) deliberately ran
without inter-agent gates: all five passes ran back to back and everything
lands in **one** end review. Live deviations, and what they cost:

- **Criteria gate: RESTORED (2026-08-29) and now always-on.** The four
  validation-run criteria were written and turned into specs in one pass; they
  now carry `approved: false` frontmatter awaiting the human's flip — most
  visibly `help/card-grid.md` Scenario 3, which pins the known card/sidebar
  Deep Reports inconsistency as expected behavior. Their specs stay in the
  suite (already reviewed + passing); the flag records that the product
  judgments await sign-off.
- **No per-ticket approval yet.** All drafts sit at `status: draft`; the
  Linear **workspace** `testah` exists (linear.app/ah-lineartestagent) but
  the MCP session must be OAuth'd to it before the Steward can file.
- **A git remote is configured**; branch-and-PR discipline
  (`scout/<date>`, `author/<date>`) applies from here on.
- **The seed failure was deleted 2026-08-29** after triage proved the path;
  the suite is fully green.
- **Suite runs against live staging.** `playwright.config.ts` supplies the
  repository's example base URL unless `TESTAH_BASE_URL` overrides it. CI
  passes no env or secrets. It works today because every spec is anonymous
  and read-only; the first
  authenticated role needs a `*.setup.ts` project and a secrets path that does
  not exist yet (`tests/fixtures/` is empty).

When the loop goes production, restore the gates in the order they appear in
the table above — criteria first (done 2026-08-29).

## Setup

New project? `bash setup.sh` after cloning — an interactive wizard that
verifies or replaces the existing `origin` (important when cloning the upstream
`template` branch); requires a human-initialized remote `master`; and creates
only `staging` from that branch when needed. It never creates or pushes
`master`. The wizard then installs the toolchain (pnpm + Playwright, uv +
crawl4ai); writes your first target into `targets.yaml` (and the Playwright
baseURL); optionally connects Linear (validates the API key against
api.linear.app and stores it in the gitignored `.env`); and prints the command
menu. Skippable per-step, safe to re-run; it refuses to clobber a customized
`targets.yaml` without asking.

## The Claude Code harness

Claude Code is the reference harness, and the repo ships a thin, committed
configuration for it (`CLAUDE.md` + `.claude/`). Everything in it POINTS at
`agents/*.md` — the harness-agnostic source of truth — and never restates it.

- **Slash commands** (`.claude/skills/`): `/scout <target>`,
  `/author <target>`, `/triage <run-id>`, `/steward`, `/loop-status`
  (read-only artifact-grounded state report). All are human-only triggers
  (`disable-model-invocation: true`) — the model cannot fire a pass on its
  own, preserving the human-gated loop.
- **Typed Reviewer** (`.claude/agents/reviewer.md`): the Author's checkpoint
  spawn targets `subagent_type: reviewer` — fresh context guaranteed by the
  harness, tools restricted to Read/Grep/Glob/Write (it can write its
  `reviews/<date>.md` verdict but structurally cannot edit code or run
  shell). Scout/Author/Steward deliberately have NO agent types: they are
  human-started top-level passes, and subagents cannot spawn subagents (an
  Author-as-subagent could not spawn its Reviewer).
- **Permissions** (`.claude/settings.json`): routine loop commands (pytest,
  playwright, the scripts CLIs, git/gh basics) are pre-approved; edits to
  the human-owned law files (`RULES.md`, `targets.yaml`, `CLAUDE.md`,
  `.claude/`) always prompt the human (ask-gate). Known limit: permission
  rules do not cover Bash-mediated writes (`sed -i`, `>>`) — the agent-file
  prose remains the primary defense; a PreToolUse Bash scan is backlog
  hardening.
- **Regression tripwire** (`.claude/hooks/pytest-tripwire.sh`): after any
  Edit/Write to `scripts/*.py`, the sub-second unit suite runs; on failure
  the hook exits 2 with pytest output so the session sees the breakage
  immediately. Fails open when `uv` is absent (adopters without the
  toolchain).
- **Personal overrides** go in `.claude/settings.local.json` (gitignored) —
  never in the committed settings.
- **Delivery guardrails** (`AGENTS.md` plus GitHub branch protection): agents
  work through feature PRs into `staging`, request one Codex review there, and
  stop at the human-only `staging` → `master` promotion PR. Direct pushes to
  both protected branches are mechanically rejected.
- **Standing rule:** any harness change updates THIS section in the same
  commit, and framework paths (including `.claude/`, `AGENTS.md`, and
  `CLAUDE.md`) sync to the `template` branch automatically.

Other LLM harnesses ignore all of this and use `agents/*.md` directly (see
README "Running the agents on your LLM platform").

## The coverage map

`docs/coverage/` holds the living visual state of the loop — one pair of
files per target in `targets.yaml`:

- **`docs/coverage/<target>.html` — the real map.** Open it in a browser
  (`open docs/coverage/example.html`). One section per designated page, one
  card per feature, and inside each card the ACTUAL tests that implement it
  (the individual test titles from the last run, each with its own status
  dot). The card's accent says where the feature stands: green passing, red
  failing, amber flaky, blue criteria written but no tests yet, dashed grey
  ticket-draft-only, grey not run — plus a plain-language note when you owe
  it something ("criteria awaiting your approval", "ticket draft only",
  "⚠ over flake threshold"). The map is a pan/zoom surface: drag to pan
  (mouse or touch), scroll to zoom at the cursor once you have touched the
  map, pinch on a trackpad or touchscreen, or use the +/−/reset toolbar.
  The file is fully self-contained — inline CSS and JS, no network requests
  — so it works from disk, in a sandbox, or attached to a PR.
- **`docs/coverage/<target>.md` — the flat companion**, for GitHub (which
  cannot run the html): `page | feature | tests | last run | notes`, with
  scaffolding specs listed at the bottom. No mermaid.

Both are generated, never hand-edited: `uv run python -m scripts.coverage_map`.
The Author (Mode B) regenerates them in every triage commit. A draft the
Author has implemented is hidden from the map once the draft's frontmatter
gains `implemented: <requirements path>` (the Author sets this when
consuming it).

## The template branch

`template` is the shareable, project-data-free starter: framework only
(agents/, scripts/, config, generic docs, placeholder `targets.yaml`), none
of any target's page-maps/requirements/specs/tickets/triage/critiques/
flake-history. New adopters clone it and point `targets.yaml` at their app.

Maintenance is AUTOMATED: `.github/workflows/template-sync.yml` runs on
every push to `master` and checks out only framework paths onto `template`
(agents, scripts, dashboard, .github, AGENTS.md, .mcp.json, package/lock files,
RULES.md, README, `docs/spec.md`, `docs/running-the-loop.md`, and the dashboard's exact
POM/requirement/page map).
Manual fallback, same paths after the dashboard exists:

    git checkout template
    git checkout master -- scripts/sync_template_paths.sh
    bash scripts/sync_template_paths.sh master
    uv run pytest -q && git add -A && git commit -m "sync framework from master"
    git checkout master

The sync workflow is guarded to run only in the upstream testah repo — in a
project created from the template it inherits harmlessly as a no-op (delete
it there if you prefer a clean Actions list).

Never broadly checkout project-data paths (`targets.yaml`, `page-maps/`,
`requirements/`, `tests/specs/`, `tests/pages/`, `tickets/`, `triage/`,
`critiques/`, `reviews/`, `flake-history.json`, `changed-pages.json`,
`docs/plans/`, `docs/review-packet-*`, `docs/coverage/`) onto
`template`. Only the exact dashboard support files listed above are exceptions;
all target-specific artifacts remain excluded.
