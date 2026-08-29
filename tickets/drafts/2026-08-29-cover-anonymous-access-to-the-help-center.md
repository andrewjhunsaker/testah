---
type: test-feature
target: vizaeo
source: page-maps/vizaeo/help
status: draft
---
# Cover anonymous access to the Help Center

**Feature.** `/help` and all ten `/help/*` articles serve 200 to an
unauthenticated visitor. This is a deliberate exception to the app's default
posture: `/dashboard` (and `/` on staging) 307 to
`/login?redirect_url=…` for the same anonymous session.

**Why it needs coverage.** The docs are public sales/support surface — an
auth-middleware matcher change that accidentally swallows `/help` would gate the
entire help center behind login with no loud failure, and nothing else in the
suite would notice. Cover: an anonymous request to `/help` and each `/help/*`
route returns 200 (not 307 to `/login`), and the rendered page contains the
`h1` "Help Center".

Related observation for the product side (not this test): both top-bar links on
`/help` — the "Vizaeo" wordmark and "← Back to app" — point at `/dashboard`,
and there is no `<footer>`, so an anonymous reader who lands on the docs has no
working way back to any public page. Worth a product-bug draft separately.

**Source.** `page-maps/vizaeo/help/features.md` ("What the page is for",
"Broken / suspect" item 3).
