# Review packet — first full loop, 2026-08-28 (validation run)

One-stop index for the single human gate. Every artifact below is committed
on `master`; review in any order, but the Steward's summary in
`critiques/2026-08-28.md` + this file is the fastest path.

## The run, in commit order

| Stage | Commit | Artifacts |
|---|---|---|
| Scout (crawl + judge, 2 pages) | `3e7cc3d` | `page-maps/vizaeo/{help,pricing}/` (5 files each), `changed-pages.json` (2 new), 10 `test-feature` drafts in `tickets/drafts/` |
| Author Mode A (criteria → POMs → specs, Reviewer-passed) | `94ff067` | `requirements/vizaeo/**` (4), `tests/pages/` (4 POMs), `tests/specs/` (4 specs), `reviews/2026-08-28*.md` (2 rounds), mailbox cleared |
| Seed failure planted | `52d9362` | `tests/specs/seed-failure.spec.ts` |
| Agentless run (no agent involved) | — | 34 executions, 33 passed, seed failure failed + retried, `reports/last-run.json` |
| Author Mode B (triage) | `470919e` | `triage/local-2026-08-28.md` (verdict: script-issue, 7-point evidence chain), `flake-history.json` baseline |
| Steward (close) | `162ca21` | 2 `framework-update` drafts, `critiques/2026-08-28.md`, `docs/running-the-loop.md` |

## Decisions needed (Andrew)

1. **Create the Linear project `testah`** — 12 drafts wait at `status: draft`;
   nothing files until it exists. Approve a draft by flipping its `status:`
   to `approved` (the Steward files it and stamps `filed:<id>`).
2. **Create the GitHub remote + push** (`git remote add origin
   git@github.com:andrewjhunsaker/testah.git && git push -u origin master`).
   First CI run will be red on the seed failure unless #3 ships in the same
   push.
3. **Delete the seed spec** after review: `git rm tests/specs/seed-failure.spec.ts`.
4. **Three failing-by-design drafts** (CLS budget, mobile-drawer a11y,
   console-clean) — schedule the fixes, ratchet the thresholds, or defer;
   don't approve as ordinary coverage.
5. **Two framework drafts** — crawler's false `status_code: 307`
   (`record-the-true-http-status-in-page-json`), and the SignupPage
   page-map carve-out decision (`resolve-the-signup-pom-page-map-gap`).

## Product findings on staging (from Scout's judge pass — no tickets yet by design)

- `/help` CLS **0.2788** ("poor"; card grid reflows after first paint).
- Logged-out dead-end: help's wordmark + "Back to app" both 307 to `/login`;
  `/pricing` has exactly one link (`/signup`) and no navigation at all.
- Sidebar links 10 articles, grid shows 9 (Deep Reports card missing) —
  pinned as expected in the criteria; fixing it flips a test red on purpose.
- Site-wide `favicon.ico` / `icon-192.png` 404s + manifest warning.
- Mobile drawer: no Escape-close, no scroll lock, no `aria-expanded`.

## Design gaps surfaced by the run (in `critiques/2026-08-28.md`)

- Scout-observed product defects with no failing test have **no ticket path**
  (they die between Scout and Steward) — needs a design decision.
- First gate to restore in production mode: **criteria approval** (agents
  pinned product judgments unreviewed this run).
- CI e2e hits live staging with no secrets/base-URL plumbing — resolve
  before relying on the pushed workflow.

## Validation-mode deviations (restored in production runs)

Collapsed gates (criteria approval, ticket approval, per-stage PRs), direct
commits to `master` (no remote), Linear dedup/filing skipped (no project),
Playwright MCP stood in for Chrome DevTools MCP.
