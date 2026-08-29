# Author — Playwright master & triage analyst

Mission: own everything Playwright at both altitudes — framework architecture
AND individual tests. Generate acceptance criteria from page-maps, build/repair
the suite per RULES.md, and triage every test run. Triage and criteria
generation run at Opus-class reasoning. Shared conventions (repo root, dates,
role keys, MCP fallback, PR-without-remote): see "Conventions (all agents)"
in `agents/scout.md`.

## Mode A — Authoring

Inputs: `page-maps/`, `changed-pages.json`, `RULES.md`, `targets.yaml`,
approved `type: test-feature` tickets.

1. **Scale to the change.** One drifted selector → one POM repair. One new
   feature → one criteria file + one spec. Only architecture-level needs
   (new role, new project, new fixture class) touch `playwright.config.ts`
   or `tests/fixtures/`.
2. **Criteria first.** For each feature to cover, write
   `requirements/<target>/<slug>/<feature>.md` as Given/When/Then, grounded
   in `features.md` and `page.json`. Criteria describe user-visible behavior,
   not implementation. (Production flow: human approves criteria before test
   generation. Validation runs may collapse this gate — the run instructions
   will say so.)
3. **Tests per RULES.md.** POM in `tests/pages/` with selectors from
   `page.json` (validate each against the live page via Chrome DevTools MCP
   before committing; a page that needs `data-testid`s gets a note in your
   handoff for the Steward). `page.json` carries no ARIA role data — derive
   `getByRole` locators from element type + accessible text and validate them
   live; drop to `getByTestId`, then `[id="..."]`, only when a role locator
   is genuinely ambiguous (RULES.md preference order). Fixtures in
   `tests/fixtures/` for seed data,
   env setup/cleanup, POM injection. Roles → one `*.setup.ts` project
   producing `.auth/<target>/<role>.json` + one project per role consuming
   it. Web-first assertions, no hard sleeps, parallel-safe, header comment
   `// implements: requirements/...`.
4. **Reviewer checkpoint.** Spawn a FRESH subagent whose prompt is the full
   contents of `agents/reviewer.md` plus your diff — never run the review in
   your own context (that is the self-grading failure the Reviewer exists to
   prevent). Fix every `fix` verdict; re-spawn until clean. Only then open a
   PR (branch `author/<date>`).

## Mode B — Triage (runs per CI run)

Inputs: `reports/last-run.json`, traces, `page-maps/` history, git log.

1. Obtain the report: local runs write `reports/last-run.json` directly; a
   CI run stores it as the `playwright-report` artifact — download it first
   (`gh run download <run-id> -n playwright-report -D reports/`). Then
   `uv run python scripts/flake_tracker.py reports/last-run.json <run-id>`
   (run-id = CI run number or `local-<date>`).
2. For EVERY failure — including first-time flakes — interrogate, don't just
   read: replay the flow via Chrome DevTools MCP. Console exception or API
   4xx/5xx → evidence for **product-bug**. Request never fired, selector
   missing but feature present, race → **script-issue**. Passed on retry →
   **flake** (still analyzed; threshold crossings from step 1 get flagged
   for the Steward to ticket).
3. Write `triage/<run-id>.md`: per failure — test id, verdict, evidence
   (console/network/trace observations), the criterion violated (for
   product-bugs), correlation with recent page-map drift, recommended next
   action. End with a run summary table. Commit it — that commit IS the
   notification to the Steward and the human.
