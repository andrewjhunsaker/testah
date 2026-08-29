---
type: test-feature
target: vizaeo
source: page-maps/vizaeo/pricing
status: draft
---
# Pin the /pricing figures to pricing config

**Feature.** The primary offer card on `/pricing` renders the price **$89**
with the note "one-time purchase", and the inclusion bullet
"🏆 10 competitors included, $10 each for more". In the RSC payload the numbers
arrive as separate interpolated children (`["🏆 ", 10, " competitors included, ",
"$10", " each for more"]`), i.e. they are bound to pricing config rather than
written into prose.

**Why it needs coverage.** Price is the single highest-consequence string on the
public site, and the repo's own rule is that prices/counts always render from
`PRICING` and are never hardcoded. A test should assert the rendered figures
match the pricing source of truth — so that a config change either propagates
here or fails loudly, and so nobody can "fix" a stale price by typing a literal
into the JSX. Cover: displayed price, the "one-time purchase" framing, included
competitor count, and per-extra-competitor price, all read from config rather
than asserted as magic numbers in the test.

**Source.** `page-maps/vizaeo/pricing/features.md` (features 2 and 4),
`page-maps/vizaeo/pricing/page.md`.
