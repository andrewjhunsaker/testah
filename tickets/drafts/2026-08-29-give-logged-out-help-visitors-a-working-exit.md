---
type: product-bug
target: vizaeo
source: page-maps/vizaeo/help
status: draft
---
# Give logged-out /help visitors a working exit

**Observed behavior.** `/help` is publicly reachable without authentication,
but both links in its top bar — the "Vizaeo" wordmark and the right-aligned
"← Back to app" link — point at `/dashboard`, which 307s an anonymous session
to `/login?redirect_url=%2Fdashboard`. There is no `<footer>` on the page
either, so neither top-bar link nor any other in-page element gives a
logged-out reader a route back to marketing content.

**Where.** `/help` doc-shell top bar (both links) and absence of a footer.

**Evidence** (`page-maps/vizaeo/help/features.md`):
"**Both top-bar links dead-end for anonymous visitors.** The 'Vizaeo' wordmark
and '← Back to app' both point at `/dashboard`, which 307s to
`/login?redirect_url=%2Fdashboard`. `/help` is publicly reachable, so a
logged-out reader has no working way back to marketing content — there is no
`<footer>` on the page either."

**Expected behavior.** An anonymous visitor on a public page should have at
least one working route out — e.g. the wordmark linking to `/` (the marketing
homepage) instead of `/dashboard`, or a footer with marketing/help links that
don't require a session.

**Impact.** `/help` is the one page staging lets anonymous visitors reach
directly; today it is a dead end for them once they arrive — every exit
bounces through a login wall. This compounds the related `/pricing`
no-navigation defect: neither public page routes a non-converting visitor
anywhere else, including to each other.
