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
| 3 | **Agentless run** — `pnpm exec playwright test` | CI on push/PR, or a human locally | `tests/`, `playwright.config.ts` | `reports/last-run.json`, `reports/html/` (both gitignored) |
| 4 | **Author Mode B** — `agents/author.md` | human, per run that produced failures | `reports/last-run.json`, traces, page-map history, git log | `triage/<run-id>.md`, `flake-history.json` |
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

    # Framework's own tests
    uv run pytest -v

`scripts/flake_tracker.py` prints one line per test at or over **3 flaky
results in the last 10 runs**; silence means no crossing. It is idempotent —
reprocessing the same report under the same run-id does not double-count.

CI is `.github/workflows/tests.yml`: `scripts-unit` (pytest) and `e2e`
(Playwright, chromium), on push to `master` and on every PR. `e2e` uploads
`reports/` as the `playwright-report` artifact even on failure — that artifact
is Mode B's input.

## Gates in PRODUCTION mode

Per [spec.md §11](spec.md). Each is a human stop, not a notification:

| Gate | Who | What |
|---|---|---|
| Page-map updates | Human | PR carrying the drift summary — never raw DOM |
| Acceptance criteria | Human | **before** any test is generated from them |
| Test framework changes | Reviewer (floor) → Human (merge) | PR |
| All Linear tickets | Human flips `status: draft` → `approved`; the Steward then files and sets `status: filed:<id>` | `tickets/drafts/` |
| Critique adoption | Human | which recommendations become work |

Tickets go to the Linear project named **testah** — including product bugs
found in targets. A target with `ticketing: direct` in `targets.yaml` skips the
draft step and files immediately; `vizaeo` is `draft`.

Agents never edit `RULES.md` or `targets.yaml`. Both are human-owned law.

## Current validation-mode deviations

The first iteration (`docs/plans/2026-08-28-testah-v1.md`) deliberately ran
without inter-agent gates: all five passes ran back to back and everything
lands in **one** end review. Live deviations, and what they cost:

- **No criteria-approval gate.** The four files in `requirements/` were written
  and turned into specs in the same pass. They encode product decisions — most
  visibly `help/card-grid.md` Scenario 3, which pins the known card/sidebar
  Deep Reports inconsistency as expected behavior. Restore this gate first.
- **No per-ticket approval.** All twelve drafts sit at `status: draft`; nothing
  has been filed, and nothing can be — the **Linear project `testah` does not
  exist yet**.
- **Commits go straight to `master`.** There is **no git remote**, so no PR
  exists for any pass and CI has never run. Branch-and-PR discipline
  (`scout/<date>`, `author/<date>`) starts at the first push.
- **A deliberate failure is planted.** `tests/specs/seed-failure.spec.ts`
  (`@seed-failure`) exists only to exercise triage; `RULES.md` sanctions the tag
  for exactly that. It makes the suite red until deleted, which the plan expects.
- **Suite runs against live staging.** `playwright.config.ts` defaults
  `baseURL` to `https://staging.vizaeo.com` and CI passes no env or secrets. It
  works today because every spec is anonymous and read-only; the first
  authenticated role needs a `*.setup.ts` project and a secrets path that does
  not exist yet (`tests/fixtures/` is empty).

When the loop goes production, restore the gates in the order they appear in
the table above — criteria first.
