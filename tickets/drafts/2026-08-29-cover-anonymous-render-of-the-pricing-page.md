---
type: test-feature
target: vizaeo
source: page-maps/vizaeo/pricing
status: draft
---
# Cover the anonymous render of /pricing

**Feature.** `/pricing` serves 200 to an unauthenticated visitor and renders the
full offer — hero `h1` "Your competitors are showing up in AI answers. Are
you?", the primary offer card, and the CTA — with no auth redirect, in a session
with no cookies.

**Why it needs coverage.** `/pricing` is the top of the funnel; on staging `/`
already 307s to `/login`, so the boundary between public marketing routes and
gated app routes is live and moves with middleware changes. If `/pricing` ever
lands on the gated side, paid acquisition traffic hits a login wall silently.
Cover: anonymous 200 (not 307 to `/login`), hero `h1` and offer card present,
and no console **errors** on load.

The console-error assertion needs one prior cleanup or an explicit allowlist:
the current anonymous load logs `GET /icon-192.png` → **404** plus the
matching manifest-icon warning, and `GET /favicon.ico` → **404** (observed on
`/help` in the same session; site-wide, not page-specific). Also present, and
expected on staging: `[PostHog] API key not found. Analytics disabled.` and two
"preloaded but not used" CSS warnings.

**Source.** `page-maps/vizaeo/pricing/features.md` ("What the page is for",
"Broken / suspect" console bullet).
