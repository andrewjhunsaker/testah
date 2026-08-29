---
type: test-feature
target: vizaeo
source: page-maps/vizaeo/help
status: draft
---
# Cover the /help mobile navigation drawer

**Feature.** Below the sidebar breakpoint (verified at 390x844) the doc-shell
top bar shows a 44x44 hamburger `button[aria-label="Toggle navigation"]`
(`.help-hamburger`, `display:none` at desktop width). Clicking it renders the
sidebar as a fixed 260px `<aside>` (`z-index:50`) carrying all 11 nav links,
over a full-viewport backdrop (`z-index:40`). Clicking the backdrop closes it.

**Why it needs coverage.** This is the entire navigation for the docs on
mobile, and it is only reachable through interaction — no static crawl sees it.
It also has three behaviors that are currently missing and that a test should
assert as the expected contract (each will fail until fixed):

- `Escape` does not close the drawer — the `<aside>` stays `display:block`.
- No body scroll lock while open (`body { overflow: visible }`); the page
  scrolls behind the drawer.
- The toggle exposes no `aria-expanded`, and focus is not moved into the drawer
  on open (`document.activeElement` remains the hamburger).

Cover: hidden at desktop width / visible at mobile width, open reveals all 11
links, backdrop click closes, plus the three assertions above.

**Source.** `page-maps/vizaeo/help/features.md` (feature 5 and the "Mobile
drawer a11y/behavior gaps" bullet).
