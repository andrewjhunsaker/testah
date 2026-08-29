# RULES.md — human-owned testing conventions

The Author and Reviewer treat this file as law. Humans edit it; agents never do.

## Test types enabled
- e2e (Playwright) — ON
- API, contract, property, visual — OFF until turned on here

## Page Object Model
- Required for every spec. POMs live in `tests/pages/`, one class per page,
  named `<Slug>Page` (e.g. `HomePage`).
- Selectors come from the page-map (`page-maps/<target>/<slug>/page.json`). Preference order:
  `getByRole` > `getByTestId` > CSS id. Raw text/CSS selectors need a
  justifying comment.

## Discipline
- Web-first assertions only (`await expect(...)`) — no hard sleeps, no
  `waitForTimeout`.
- Every test independent and parallel-safe: no shared mutable state, no
  order dependence.
- Auth via storageState in `.auth/<target>/<role>.json`, produced by a
  `*.setup.ts` project — never a login flow inside a functional test.
- Tags: `@smoke` (critical path), `@flaky` (Author-applied while a fix is
  pending), `@seed-failure` (deliberate failures for loop validation only).

## Traceability
- Each spec file header comments the acceptance criterion it implements:
  `// implements: requirements/<target>/<slug>/<feature>.md`

## Bootstrap exception
- `tests/specs/smoke.spec.ts` predates the loop: it is a scaffold health
  check, exempt from the POM and traceability rules above. Every
  agent-authored spec MUST comply. No other exemptions exist.
