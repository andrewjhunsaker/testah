---
type: test-feature
target: vizaeo
source: page-maps/vizaeo/help
status: draft
---
# Guard the /help index against layout-shift regression

**Feature.** Initial render of the `/help` index — the doc shell plus the
article card grid.

**Why it needs coverage.** Measured CLS on `/help` is **0.2788**, which is in
the "poor" Core Web Vitals band (>0.25), reproduced identically across two
independent anonymous loads. It is a single shift at t≈203ms whose reported
sources are `MAIN.help-content` and four `A.…__card` nodes — the card grid
reflows after first paint. LCP is healthy (240–1316ms), so layout stability is
the only perf defect here.

Cover with a CLS budget assertion on `/help` (suggested threshold: ≤0.1, the
"good" band) measured via `PerformanceObserver({type:'layout-shift',
buffered:true})`. Note this test fails against the current build by design —
it pins the fix and prevents the regression from returning. If the fix is not
scheduled, land it at ≤0.28 as a ratchet and tighten later rather than not
covering it at all.

**Source.** `page-maps/vizaeo/help/perf.json`,
`page-maps/vizaeo/help/features.md` ("Broken / suspect" item 1).
