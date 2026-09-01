# Session handoff — 2026-09-01

State of testah + the showcase effort, for any session (Claude Code, Codex,
or other) picking this up. Read alongside `docs/running-the-loop.md` and
`docs/plans/2026-08-31-showcase-loop.md`.

## Where things stand

- **testah v1.0** — built, validated, pushed: github.com/andrewjhunsaker/testah
  (PRIVATE; publishing decision deferred). Branches: `master` (working repo,
  contains Vizaeo-staging artifacts), `template` (clean project-agnostic
  starter, auto-synced from master by `.github/workflows/template-sync.yml`,
  guarded to run only in the upstream repo).
- **First full loop closed** against Vizaeo staging (help + pricing pages):
  page-maps, 4 approved-shape criteria (still `approved: false` — awaiting
  Andrew's flip), 4 POMs, 33-test suite green vs live staging, seed failure
  correctly triaged as script-issue then deleted, coverage maps generated.
- **Harness committed**: CLAUDE.md + `.claude/` — slash commands `/scout
  /author /triage /steward /loop-status` (human-only), typed `reviewer`
  agent (Read/Grep/Glob/Write, opus), ask-gates on RULES.md / targets.yaml /
  CLAUDE.md / .claude, pytest tripwire hook. `agents/*.md` is the sole
  source of truth; `.claude` files are pointers.
- **One-command onboarding**: `bash setup.sh` (remote → deps → first target
  → Linear key w/ live validation → command menu). Tested on the skip path;
  fresh-machine happy path NOT yet exercised (the showcase bootstrap is the
  planned first real test).
- **Ticket state**: ~20 drafts in `tickets/drafts/` (local-first queue by
  design). Linear workspace `testah` exists (linear.app/ah-lineartestagent)
  but NO key provided yet — `LINEAR_API_KEY` in `.env` (or MCP OAuth) is
  needed before `uv run python -m scripts.file_tickets` can drain the queue.
- **Unit suite**: 22 pytest tests green. CI (`tests` + `template-sync`)
  green on master.

## Open decisions on Andrew

1. Flip the four criteria files to `approved: true` (or adopt the proposed
   benchmark-run gate model instead — spec'd, not wired).
2. Provide `LINEAR_API_KEY` (testah workspace) → drain the draft queue.
3. Three failing-by-design drafts (CLS budget, drawer a11y, console-clean):
   schedule / ratchet / defer.
4. Publishing testah publicly — deferred; leading option was template as
   default branch.
5. Refine the showcase-loop draft (below) — this is the active workstream.

## Active workstream: the showcase loop (draft v0.1, awaiting refinement)

`docs/plans/2026-08-31-showcase-loop.md`. Two portfolio projects that
cross-sell:
- **Project 1**: testah as a product — static self-contained
  `docs/dashboard.html` via `scripts/dashboard.py` + `--serve` (decided),
  "Needs you" section first, perf-history.jsonl prerequisite for
  benchmarks; README "use it in 10 minutes" + one command table.
- **Project 2**: `toolshop-showcase` repo vs practicesoftwaretesting.com
  (decided) — bootstrapped via template + setup.sh as unassisted-user
  role-play, RULES.md rewritten as Andrew's industry-standards spec (his
  gate), three loop iterations (anonymous → RBAC first-ever → depth:
  checkout/API/a11y), README credits testah (decided).
- Meta-loop: showcase friction → testah framework tickets → template sync →
  showcase pulls. Done-signal: an iteration with zero upstream tickets.
- Five open questions at the doc's end (dashboard v1 scope, cross-repo
  ticket routing / `bug_destination` graduation, screenshots vs template
  sync, visual+a11y scope, demo recording) — with recommendations inline.
- Recommended sequencing: dashboard BEFORE showcase bootstrap (the dashboard
  screenshot inside the showcase flow is the strongest portfolio artifact).

## Standing rules (do not violate)

- No AI attribution on commits/PRs (enforced in ~/.claude/settings.json too).
- Harness changes update docs/running-the-loop.md in the SAME commit;
  framework paths auto-sync to template — never sync project-data paths.
- Criteria-approval gate is always-on; criteria never silently updated
  (behavior-change verdict → human decides).
- Scout flags are validated by the Steward before reaching the human.
- testah is project- and tracker-agnostic; Vizaeo and Linear are reference
  targets/implementations only.
