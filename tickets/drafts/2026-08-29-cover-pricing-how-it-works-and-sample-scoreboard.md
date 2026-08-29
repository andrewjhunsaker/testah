---
type: test-feature
target: vizaeo
source: page-maps/vizaeo/pricing
status: draft
---
# Cover the /pricing "How it works" and sample-scoreboard sections

**Feature.** Two static explanatory sections between the offer card and the FAQ:

- **How it works** — three numbered steps: (1) "Enter your business details and
  top competitors.", (2) "We check how 5 AI platforms rank you vs competitors.",
  (3) "Get your scoreboard + a Visibility Improvement Checklist with what to fix
  first."
- **Sample scoreboard preview** — three illustrative stat tiles: "Overall AI
  visibility 72 / 100", "Competitor benchmark +14%", "Highest-impact action —
  Improve service page intent matching".

Plus the "Know exactly what to do next" section describing the Visibility
Improvement Checklist as a prioritized, points-ranked action list.

**Why it needs coverage.** These sections make product claims that must stay
true as the product changes — the "5 AI platforms" count in particular is a fact
pinned elsewhere by the docs-drift contract, and the sample tiles are the only
place a prospect sees what a score looks like. Cover: all three steps render in
order, the platform count matches the platform config rather than a hardcoded
literal, the three stat tiles render with labels and values, and the sample
figures are visibly framed as a sample (they are static, not live data).

**Source.** `page-maps/vizaeo/pricing/features.md` (features 5, 6, 7).
