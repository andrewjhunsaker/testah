---
type: product-bug
target: vizaeo
source: page-maps/vizaeo/help
status: draft
---
# Add the missing Deep Reports card to the /help grid

**Observed behavior.** The `/help` sidebar navigation lists 11 links (the
index plus 10 articles), including "Competitor Deep Reports" →
`/help/deep-reports`, which returns 200. The card grid on the same page shows
only 9 article cards — there is no card for Deep Reports. Sidebar and grid
disagree on how many articles exist.

**Where.** `/help`, sidebar nav vs. main card grid.

**Evidence** (`page-maps/vizaeo/help/features.md`):
"**'Competitor Deep Reports' is missing from the card grid.** The sidebar
links `/help/deep-reports` (which returns 200), but no card exists for it —
the grid has 9 cards against the sidebar's 10 articles. Content/nav
inconsistency."

**Expected behavior.** The card grid should include a tenth card for
"Competitor Deep Reports" linking to `/help/deep-reports`, matching the
sidebar's article list one-for-one.

**Impact.** Desktop visitors browsing by card (the primary discovery surface
per the page map) cannot find the Deep Reports article at all unless they
already know to look in the sidebar — the article is effectively undiscoverable
from the main content area.

**Note.** `requirements/vizaeo/help/card-grid.md` (Scenario 3, currently
`approved: false`) deliberately pins today's 9-card grid and the sidebar/grid
mismatch as *expected* behavior: "the card grid carries no card for Deep
Reports — the single known content/nav inconsistency, pinned deliberately."
Fixing this defect means the criteria file's Scenario 3 (and its 9-row table)
also needs updating to a 10-card grid — a behavior-change decision, not just a
code fix, and should go back through the criteria-approval flow rather than
being implemented against the currently-pinned spec.
