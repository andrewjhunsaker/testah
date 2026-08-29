---
type: product-bug
target: vizaeo
source: page-maps/vizaeo/pricing
status: draft
---
# Add navigation to /pricing

**Observed behavior.** `/pricing` — the public, unauthenticated sales page for
the AI Visibility Report — renders as a single-column `<main>` with zero
`<nav>`, no `<header>`, no `<footer>`, and exactly one `<a>` on the entire
page: the "Get Your Visibility Scoreboard" CTA to `/signup`. A visitor who
isn't ready to sign up has no other in-page destination, including no link to
`/help`.

**Where.** `/pricing`, page-wide (no chrome present at all).

**Evidence** (`page-maps/vizaeo/pricing/features.md`):
"**No navigation whatsoever.** Zero `<nav>`, no header, no footer, and one
single `<a>` on the page. A visitor who does not want to sign up has no
in-page route anywhere else — including no link to `/help`, which matches the
known help-discoverability gap."

**Expected behavior.** A public sales page should offer at least a minimal
route elsewhere for non-converting traffic — e.g. a header wordmark to the
marketing homepage and/or a footer with a link to `/help`, without diluting
the single-CTA design intent.

**Impact.** Every visitor who lands on `/pricing` and isn't ready to convert
on `/signup` right away is stranded — they cannot get to help content, the
homepage, or anywhere else short of using the browser back button. Combined
with the `/help` exit-dead-end defect, the two public pages that don't require
auth have no route between them.
