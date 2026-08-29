---
type: test-feature
target: vizaeo
source: page-maps/vizaeo/pricing
status: draft
---
# Cover the /pricing FAQ accordion

**Feature.** Four native `<details>/<summary>` items under the "FAQ" heading,
all collapsed on load: "What do I get after purchase?", "Is this a monthly
subscription?", "How quickly is the visibility scoreboard delivered?", "Is my
payment and business data secure?". Verified live: clicking a summary expands
that item and reveals its answer paragraph; items open independently (no
single-open group behavior).

**Why it needs coverage.** The answers carry commercial claims a buyer relies on
— "not a subscription", "delivered in minutes", "secure checkout" — and they are
invisible to any static capture, since the answer text is absent from the
accessibility tree until expanded. Cover: all four summaries render collapsed on
load, clicking one reveals its answer, the answer text matches the copy of
record, and a second item can be open at the same time (pin the current
independent-open behavior so a redesign to single-open is a conscious change).

**Source.** `page-maps/vizaeo/pricing/features.md` (feature 8).
