---
type: product-bug
target: vizaeo
source: page-maps/vizaeo/help
status: draft
---
# Fix the /help card-grid layout shift

**Observed behavior.** `/help` produces a Cumulative Layout Shift of 0.2788 —
"poor" by Core Web Vitals (>0.25) — reproducible across two independent loads.
A single shift lands at t≈203ms; its sources are `MAIN.help-content` and four
`A.…__card` elements. LCP is fine (240–1316ms), so this is isolated to the
grid reflowing after first paint.

**Where.** `/help`, the nine-card article grid below the page heading.

**Evidence** (`page-maps/vizaeo/help/perf.json`):
```
{ "lcp_ms": 240, "cls": 0.2788, "inp_ms": null, "measured_at": "2026-08-29T02:09:30+00:00" }
```
`page-maps/vizaeo/help/features.md`: "CLS 0.2788 — 'poor' by Core Web Vitals
(>0.25), reproducible. A single layout shift at t≈203ms whose sources are
`MAIN.help-content` and four `A.…__card` elements: the card grid reflows
after first paint. Same value on two independent loads. This is the one real
perf defect on the page."

**Expected behavior.** CLS ≤ 0.1 ("good" band). The grid container and card
elements should reserve their final dimensions (fixed aspect ratio / skeleton
sizing) before content paints, so nothing reflows once emoji/title/description
content loads in.

**Impact.** Every anonymous visitor to the documentation hub — the one public
page reachable without auth — takes a "poor" Core Web Vitals hit on their
first paint, which affects both real user experience and any Vitals-based
SEO signal for a page whose entire job is being findable.
