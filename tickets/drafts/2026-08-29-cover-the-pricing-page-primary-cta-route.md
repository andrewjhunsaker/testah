---
type: test-feature
target: vizaeo
source: page-maps/vizaeo/pricing
status: draft
implemented: requirements/vizaeo/pricing/primary-cta-route.md
---
# Cover the /pricing primary CTA route

**Feature.** "Get Your Visibility Scoreboard" → `/signup`. It is the **only**
`<a>` on the entire page (verified: `document.querySelectorAll('a').length === 1`).

**Why it needs coverage.** This is the whole conversion path of the public
site — signup-first, with no direct-to-checkout route from this page. If this
one href breaks or the button stops rendering, `/pricing` becomes a dead end and
no other test in the suite touches it. Cover: the CTA renders with its expected
label, its href is `/signup`, and following it reaches the signup page (200,
signup form present) — stop there; do not create an account.

Adjacent observation for the product side: the page has no `<header>`,
`<footer>`, or `<nav>` at all, so a visitor who does not want to sign up has no
in-page route anywhere else, including none to `/help`.

**Source.** `page-maps/vizaeo/pricing/features.md` (feature 3, "Broken /
suspect" item 1).
